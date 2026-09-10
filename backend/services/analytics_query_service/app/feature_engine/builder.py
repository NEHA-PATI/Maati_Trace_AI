from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Iterable

from services.analytics_query_service.app.feature_engine.math_utils import (
    as_date,
    clip01,
    finite_number,
    freshness_score,
    linear_slope,
    mad,
    median,
    robust_z,
    safe_mean,
    safe_ratio,
    safe_weighted_mean,
)

FEATURE_VERSION = "farm_h3_engineered_features_v1"

# The feature layer prefers Sentinel-2 H3 observations, then falls back to a
# successful H3-compatible optical/radar source when a sibling dataset is
# unavailable. All environmental observations are still joined into the vector.
S2_TEMPORAL_FIELDS = (
    "ndvi",
    "gndvi",
    "evi",
    "savi",
    "ndmi",
    "ndwi",
    "mndwi",
    "msi",
    "bsi",
    "nbr",
    "nbr2",
    "ndre",
    "reci",
    "fvc_proxy",
    "nirv",
)

DEFAULT_FRESHNESS_HALF_LIFE_DAYS: dict[str, float] = {
    "sentinel2": 12,
    "sentinel1": 18,
    "landsat": 28,
    "gpm": 7,
    "era5": 7,
    "smap": 5,
    "modis_et": 12,
    "modis_vegetation": 12,
    "forecast": 2,
    "terrain": 3650,
    "landcover": 365,
    "jrc_water": 3650,
    "soilgrids": 3650,
}


def _date(value: Any) -> date | None:
    try:
        return as_date(value)
    except Exception:
        return None


def _num(value: Any) -> float | None:
    return finite_number(value)


def _dedupe_h3_daily(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the best-quality/newest record for each H3/date pair."""
    best: dict[tuple[int, date], dict[str, Any]] = {}
    for row in rows:
        d = _date(row.get("snapshot_date"))
        h3_index = row.get("h3_index")
        if d is None or h3_index is None:
            continue
        key = (int(h3_index), d)
        candidate_quality = _num(row.get("valid_fraction")) or 0.0
        existing = best.get(key)
        existing_quality = _num(existing.get("valid_fraction")) if existing else None
        if existing is None or candidate_quality > (existing_quality or 0.0):
            best[key] = row
    return sorted(best.values(), key=lambda r: (int(r["h3_index"]), _date(r["snapshot_date"]) or date.min))


def _dedupe_daily(rows: Iterable[dict[str, Any]], date_key: str) -> list[dict[str, Any]]:
    best: dict[date, dict[str, Any]] = {}
    for row in rows:
        d = _date(row.get(date_key))
        if d is None:
            continue
        # Prefer the last/newest row for that day; lakehouse uniqueness normally means one.
        best[d] = row
    return [best[key] for key in sorted(best)]


def _by_h3(rows: Iterable[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("h3_index") is None:
            continue
        out[int(row["h3_index"])].append(row)
    for values in out.values():
        values.sort(key=lambda row: _date(row.get("snapshot_date")) or date.min)
    return out


def _nearest_before(
    rows: Iterable[dict[str, Any]],
    target: date,
    *,
    date_key: str,
    max_age_days: int | None = None,
) -> dict[str, Any] | None:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        d = _date(row.get(date_key))
        if d is None or d > target:
            continue
        age = (target - d).days
        if max_age_days is not None and age > max_age_days:
            continue
        candidates.append((age, row))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _covering_period(
    rows: Iterable[dict[str, Any]],
    target: date,
) -> dict[str, Any] | None:
    covering = []
    prior = []
    for row in rows:
        start = _date(row.get("period_start"))
        end = _date(row.get("period_end"))
        if start is None or end is None:
            continue
        if start <= target <= end:
            covering.append(row)
        elif end <= target:
            prior.append((target - end, row))
    if covering:
        return covering[-1]
    if prior:
        prior.sort(key=lambda item: item[0])
        return prior[0][1]
    return None


def _previous_values(
    history: list[dict[str, Any]],
    current_date: date,
    key: str,
    *,
    lookback_days: int | None = None,
) -> list[tuple[date, float]]:
    values: list[tuple[date, float]] = []
    for row in history:
        d = _date(row.get("snapshot_date"))
        value = _num(row.get(key))
        if d is None or value is None or d >= current_date:
            continue
        if lookback_days is not None and (current_date - d).days > lookback_days:
            continue
        values.append((d, value))
    return values


def _temporal_features(
    row: dict[str, Any],
    history: list[dict[str, Any]],
    profile: dict[str, Any],
) -> dict[str, Any]:
    current_date = _date(row.get("snapshot_date"))
    if current_date is None:
        return {}

    growth_window = int((profile.get("temporal_windows") or {}).get("primary_growth_window") or 30)
    out: dict[str, Any] = {}

    for key in S2_TEMPORAL_FIELDS:
        current = _num(row.get(key))
        out[key] = current
        previous = _previous_values(history, current_date, key)
        window_values = [item for item in previous if (current_date - item[0]).days <= growth_window]
        baseline_values = [v for _, v in previous]

        if previous:
            last_value = previous[-1][1]
            out[f"{key}_delta"] = None if current is None else current - last_value
        else:
            out[f"{key}_delta"] = None

        slope_points = window_values + ([(current_date, current)] if current is not None else [])
        out[f"{key}_slope"] = linear_slope(slope_points, min_samples=3)
        out[f"{key}_z"] = robust_z(current, baseline_values, min_samples=3)
        out[f"{key}_historical_median"] = median(baseline_values)
        out[f"{key}_historical_mad"] = mad(baseline_values)

    expected_ndvi = out.get("ndvi_historical_median")
    current_ndvi = out.get("ndvi")
    if expected_ndvi is not None and current_ndvi is not None and abs(float(expected_ndvi)) > 1e-6:
        out["ndvi_trajectory_deviation"] = (float(expected_ndvi) - float(current_ndvi)) / abs(float(expected_ndvi))
    else:
        out["ndvi_trajectory_deviation"] = None

    return out


def _spatial_features(
    anchor: dict[str, Any],
    same_date_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    anchor_h3 = int(anchor["h3_index"])
    for key in ("ndvi", "ndmi", "nirv"):
        current = _num(anchor.get(key))
        peers = [
            _num(row.get(key))
            for row in same_date_rows
            if int(row.get("h3_index") or -1) != anchor_h3
        ]
        peers = [value for value in peers if value is not None]
        out[f"spatial_{key}_z"] = robust_z(current, peers, min_samples=3)
    return out


def _rolling_rainfall(
    rows: list[dict[str, Any]],
    target: date,
    window_days: int,
) -> tuple[float | None, float, int]:
    start = target - timedelta(days=window_days - 1)
    relevant = [
        row for row in rows
        if (d := _date(row.get("observation_date"))) is not None and start <= d <= target
    ]
    if not relevant:
        return None, 0.0, 0
    values = [_num(row.get("precipitation_mm")) for row in relevant]
    values = [value for value in values if value is not None]
    if not values:
        return None, 0.0, len(relevant)
    observed_days = len({_date(row.get("observation_date")) for row in relevant})
    coverage = clip01(observed_days / max(1, window_days))
    return sum(values), coverage, observed_days


def _historical_rolling_rainfall(
    rows: list[dict[str, Any]],
    target: date,
    window_days: int,
) -> list[float]:
    # Non-overlapping historical windows ending every `window_days` days. This avoids
    # over-counting highly correlated daily rolling totals while remaining transparent.
    historical: list[float] = []
    cursor = target - timedelta(days=window_days)
    earliest = min((_date(r.get("observation_date")) for r in rows if _date(r.get("observation_date"))), default=None)
    while earliest is not None and cursor >= earliest:
        value, coverage, _ = _rolling_rainfall(rows, cursor, window_days)
        if value is not None and coverage >= 0.60:
            historical.append(value)
        cursor -= timedelta(days=window_days)
    return historical


def _rain_features(rows: list[dict[str, Any]], target: date, windows: list[int]) -> tuple[dict[str, Any], float]:
    out: dict[str, Any] = {}
    coverages = []
    for days in sorted(set(windows + [3, 7, 14, 30, 60, 90])):
        current, coverage, observed_days = _rolling_rainfall(rows, target, days)
        baseline = _historical_rolling_rainfall(rows, target, days)
        baseline_median = median(baseline)
        out[f"rain_{days}d_mm"] = current
        out[f"rain_{days}d_coverage"] = coverage
        out[f"rain_{days}d_observed_days"] = observed_days
        out[f"rain_{days}d_z"] = robust_z(current, baseline, min_samples=3)
        out[f"rain_{days}d_baseline_median"] = baseline_median
        if current is not None and baseline_median is not None and baseline_median > 1e-6:
            out[f"rain_{days}d_deficit"] = clip01((baseline_median - current) / baseline_median)
        else:
            out[f"rain_{days}d_deficit"] = None
        if current is not None:
            coverages.append(coverage)
    return out, (safe_mean(coverages) or 0.0)


def _era5_rootzone(row: dict[str, Any] | None, profile: dict[str, Any]) -> float | None:
    if not row:
        return None
    weights = profile.get("root_zone_weights") or {}
    pairs = []
    for key in ("soil_water_0_7", "soil_water_7_28", "soil_water_28_100", "soil_water_100_289"):
        pairs.append((_num(row.get(key)), _num(weights.get(key)) or 0.0))
    return safe_weighted_mean(pairs)


def _era5_features(rows: list[dict[str, Any]], target: date, profile: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    latest = _nearest_before(rows, target, date_key="observation_date", max_age_days=7)
    if not latest:
        return {}, None
    history = [row for row in rows if (_date(row.get("observation_date")) or date.max) < target]
    root_current = _era5_rootzone(latest, profile)
    root_history = [_era5_rootzone(row, profile) for row in history]
    return {
        "era5_temperature_mean_c": _num(latest.get("temperature_mean_c")),
        "era5_temperature_min_c": _num(latest.get("temperature_min_c")),
        "era5_temperature_max_c": _num(latest.get("temperature_max_c")),
        "era5_dewpoint_mean_c": _num(latest.get("dewpoint_mean_c")),
        "era5_skin_temperature_c": _num(latest.get("skin_temperature_mean_c")),
        "era5_rootzone": root_current,
        "era5_rootzone_z": robust_z(root_current, root_history, min_samples=3),
        "era5_temp_max_z": robust_z(
            latest.get("temperature_max_c"),
            [row.get("temperature_max_c") for row in history],
            min_samples=3,
        ),
        "era5_skin_temp_z": robust_z(
            latest.get("skin_temperature_mean_c"),
            [row.get("skin_temperature_mean_c") for row in history],
            min_samples=3,
        ),
    }, latest


def _smap_features(rows: list[dict[str, Any]], target: date) -> tuple[dict[str, Any], dict[str, Any] | None]:
    latest = _nearest_before(rows, target, date_key="observed_at", max_age_days=5)
    if not latest:
        return {}, None
    history = [row for row in rows if (_date(row.get("observed_at")) or date.max) < target]
    root = _num(latest.get("root_zone_soil_moisture"))
    surface = _num(latest.get("surface_soil_moisture"))
    return {
        "smap_surface": surface,
        "smap_rootzone": root,
        "smap_surface_z": robust_z(surface, [r.get("surface_soil_moisture") for r in history], min_samples=3),
        "smap_rootzone_z": robust_z(root, [r.get("root_zone_soil_moisture") for r in history], min_samples=3),
    }, latest


def _modis_et_features(rows: list[dict[str, Any]], target: date) -> tuple[dict[str, Any], dict[str, Any] | None]:
    latest = _covering_period(rows, target)
    if not latest:
        return {}, None
    et = _num(latest.get("et_mm"))
    pet = _num(latest.get("pet_mm"))
    return {
        "modis_et_mm": et,
        "modis_pet_mm": pet,
        "et_pet_ratio": safe_ratio(et, pet),
    }, latest


def _modis_veg_features(rows: list[dict[str, Any]], target: date) -> tuple[dict[str, Any], dict[str, Any] | None]:
    latest = _covering_period(rows, target)
    if not latest:
        return {}, None
    history = [row for row in rows if (_date(row.get("period_end")) or date.max) < target]
    current_lai = _num(latest.get("lai"))
    current_fpar = _num(latest.get("fpar"))
    points = [(_date(row.get("period_end")) or date.min, row.get("lai")) for row in history[-8:]]
    if _date(latest.get("period_end")):
        points.append((_date(latest.get("period_end")), current_lai))
    return {
        "lai": current_lai,
        "fpar": current_fpar,
        "lai_stddev": _num(latest.get("lai_stddev")),
        "fpar_stddev": _num(latest.get("fpar_stddev")),
        "lai_z": robust_z(current_lai, [row.get("lai") for row in history], min_samples=3),
        "lai_slope": linear_slope(points, min_samples=3),
    }, latest


def _forecast_features(rows: list[dict[str, Any]], target: date) -> tuple[dict[str, Any], dict[str, Any] | None]:
    # Use the newest issue not later than the anchor and earliest forecast valid on/after it.
    eligible = []
    for row in rows:
        issued = _date(row.get("issued_at"))
        valid = _date(row.get("valid_at"))
        if issued is None or valid is None or issued > target or valid < target:
            continue
        eligible.append(row)
    if not eligible:
        return {}, None
    latest_issue = max(_date(r.get("issued_at")) for r in eligible if _date(r.get("issued_at")))
    run = [r for r in eligible if _date(r.get("issued_at")) == latest_issue]
    run.sort(key=lambda r: r.get("valid_at"))
    # Summaries from next ~72h if present.
    next72 = [r for r in run if 0 <= ((_date(r.get("valid_at")) or target) - target).days <= 3]
    first = run[0]
    return {
        "forecast_vpd": safe_mean([r.get("vapour_pressure_deficit") for r in next72]) or _num(first.get("vapour_pressure_deficit")),
        "forecast_et0_mm": safe_mean([r.get("et0_mm") for r in next72]) or _num(first.get("et0_mm")),
        "forecast_precipitation_3d_mm": sum(v for r in next72 if (v := _num(r.get("precipitation_mm"))) is not None) if next72 else _num(first.get("precipitation_mm")),
        "forecast_temperature_2m_c": safe_mean([r.get("temperature_2m_c") for r in next72]) or _num(first.get("temperature_2m_c")),
        "forecast_relative_humidity_2m": safe_mean([r.get("relative_humidity_2m") for r in next72]) or _num(first.get("relative_humidity_2m")),
    }, first


def _soil_overlap_weight(row: dict[str, Any], root_zone_weights: dict[str, Any]) -> float:
    # Convert the four ERA5 root-depth preference layers into continuous centimetre overlap weights.
    # If an admin does not configure the profile, all standard SoilGrids depths receive equal weight.
    top = int(row.get("depth_top_cm") or 0)
    bottom = int(row.get("depth_bottom_cm") or top)
    if bottom <= top:
        return 0.0
    layers = [
        (0, 7, float(root_zone_weights.get("soil_water_0_7", 0) or 0)),
        (7, 28, float(root_zone_weights.get("soil_water_7_28", 0) or 0)),
        (28, 100, float(root_zone_weights.get("soil_water_28_100", 0) or 0)),
        (100, 289, float(root_zone_weights.get("soil_water_100_289", 0) or 0)),
    ]
    total = 0.0
    for layer_top, layer_bottom, layer_weight in layers:
        overlap = max(0, min(bottom, layer_bottom) - max(top, layer_top))
        if overlap > 0 and layer_weight > 0:
            total += layer_weight * (overlap / max(1, layer_bottom - layer_top))
    return total if total > 0 else float(bottom - top)


def _soil_features(rows: list[dict[str, Any]], profile: dict[str, Any]) -> tuple[dict[str, Any], float]:
    by_property: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("quantile") or "Q0.5").upper() not in {"Q0.5", "Q50", "MEDIAN"}:
            continue
        by_property[str(row.get("property_key") or "").lower()].append(row)

    aliases = {
        "phh2o": "soil_phh2o",
        "soc": "soil_soc",
        "nitrogen": "soil_nitrogen",
        "clay": "soil_clay",
        "sand": "soil_sand",
        "silt": "soil_silt",
        "bdod": "soil_bdod",
        "cec": "soil_cec",
        "cfvo": "soil_cfvo",
    }
    out: dict[str, Any] = {}
    quality_values = []
    for property_key, output_key in aliases.items():
        prop_rows = by_property.get(property_key, [])
        pairs = []
        for row in prop_rows:
            value = _num(row.get("value"))
            weight = _soil_overlap_weight(row, profile.get("root_zone_weights") or {})
            if value is not None and weight > 0:
                pairs.append((value, weight))
                q = _num(row.get("valid_fraction"))
                if q is not None:
                    quality_values.append(clip01(q))
        out[output_key] = safe_weighted_mean(pairs)
    return out, safe_mean(quality_values) or (1.0 if any(v is not None for v in out.values()) else 0.0)


def _static_for_h3(rows: list[dict[str, Any]], h3_index: int) -> dict[str, Any] | None:
    matches = [row for row in rows if int(row.get("h3_index") or -1) == int(h3_index)]
    return matches[-1] if matches else None


def _source_quality(
    source: str,
    *,
    target: date,
    row: dict[str, Any] | None,
    valid_fraction: float | None = None,
    date_key: str | None = None,
    coverage: float | None = None,
) -> float:
    if row is None and coverage is None:
        return 0.0
    base = clip01(valid_fraction) if valid_fraction is not None else 1.0
    if coverage is not None:
        base *= clip01(coverage)
    if date_key and row:
        d = _date(row.get(date_key))
        if d is not None:
            age = max(0, (target - d).days)
            base *= freshness_score(age, DEFAULT_FRESHNESS_HALF_LIFE_DAYS.get(source, 30))
    return clip01(base)


def _source_version(row: dict[str, Any] | None) -> str | None:
    if not row:
        return None
    return str(
        row.get("processing_version")
        or row.get("source_version")
        or row.get("source_product_version")
        or ""
    ) or None


def build_feature_rows(
    *,
    farm: dict[str, Any],
    profile: dict[str, Any],
    bundle: dict[str, list[dict[str, Any]]],
    start_date: date,
    end_date: date,
    latest_only: bool = False,
) -> list[dict[str, Any]]:
    crop_code = str(farm.get("crop_code") or "").strip().lower()
    if not crop_code:
        raise ValueError("Farm crop_code is required before feature engineering")

    s2_rows = _dedupe_h3_daily(bundle.get("sentinel2") or [])
    s1_rows = _dedupe_h3_daily(bundle.get("sentinel1") or [])
    landsat_rows = _dedupe_h3_daily(bundle.get("landsat") or [])

    # Select the first successful H3 source that has data in the requested
    # window. A source may exist in the historical bundle but still be absent
    # for this run's dates, so selection must be window-aware.
    anchor_dataset = "sentinel2"
    anchor_rows = s2_rows
    for candidate_name, candidate_rows in (
        ("sentinel2", s2_rows),
        ("sentinel1", s1_rows),
        ("landsat", landsat_rows),
    ):
        if any(
            (observed_date := _date(row.get("snapshot_date"))) is not None
            and start_date <= observed_date <= end_date
            for row in candidate_rows
        ):
            anchor_dataset = candidate_name
            anchor_rows = candidate_rows
            break

    anchors = [
        row for row in anchor_rows
        if (d := _date(row.get("snapshot_date"))) is not None and start_date <= d <= end_date
    ]
    if latest_only and anchors:
        latest_date = max(_date(row["snapshot_date"]) for row in anchors)
        anchors = [row for row in anchors if _date(row["snapshot_date"]) == latest_date]
    if not anchors:
        return []

    s2_by_h3 = _by_h3(s2_rows)
    same_date_s2: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in s2_rows:
        d = _date(row.get("snapshot_date"))
        if d:
            same_date_s2[d].append(row)

    anchor_by_h3 = _by_h3(anchor_rows)
    same_date_anchor: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in anchor_rows:
        d = _date(row.get("snapshot_date"))
        if d:
            same_date_anchor[d].append(row)

    s1_by_h3 = _by_h3(s1_rows)
    landsat_by_h3 = _by_h3(landsat_rows)
    gpm = _dedupe_daily(bundle.get("gpm") or [], "observation_date")
    era5 = _dedupe_daily(bundle.get("era5") or [], "observation_date")
    smap = list(bundle.get("smap") or [])
    modis_et = list(bundle.get("modis_et") or [])
    modis_veg = list(bundle.get("modis_vegetation") or [])
    forecast = list(bundle.get("forecast") or [])

    windows = [int(v) for v in (profile.get("temporal_windows") or {}).get("rainfall", []) if int(v) > 0]
    results: list[dict[str, Any]] = []

    for anchor in anchors:
        target = _date(anchor.get("snapshot_date"))
        h3_index = int(anchor["h3_index"])
        if target is None:
            continue

        features = _temporal_features(anchor, anchor_by_h3.get(h3_index, []), profile)
        features.update(_spatial_features(anchor, same_date_anchor.get(target, [])))

        # Sentinel-1: compare closest prior ratio against prior history for this H3.
        s1_history = s1_by_h3.get(h3_index, [])
        s1_current = _nearest_before(s1_history, target, date_key="snapshot_date", max_age_days=35)
        if s1_current:
            current_ratio = _num(s1_current.get("vh_vv_ratio"))
            prior_ratios = [
                row.get("vh_vv_ratio") for row in s1_history
                if (_date(row.get("snapshot_date")) or date.max) < (_date(s1_current.get("snapshot_date")) or target)
            ]
            features.update({
                "mean_vv": _num(s1_current.get("mean_vv")),
                "mean_vh": _num(s1_current.get("mean_vh")),
                "mean_vv_db": _num(s1_current.get("mean_vv_db")),
                "mean_vh_db": _num(s1_current.get("mean_vh_db")),
                "vh_vv_ratio": current_ratio,
                "rvi": _num(s1_current.get("rvi")),
                "sar_ratio_z": robust_z(current_ratio, prior_ratios, min_samples=3),
            })

        # Landsat thermal and corroborating optical observations.
        landsat_history = landsat_by_h3.get(h3_index, [])
        landsat_current = _nearest_before(landsat_history, target, date_key="snapshot_date", max_age_days=45)
        if landsat_current:
            lst = _num(landsat_current.get("surface_temp_c"))
            prior_lst = [
                row.get("surface_temp_c") for row in landsat_history
                if (_date(row.get("snapshot_date")) or date.max) < (_date(landsat_current.get("snapshot_date")) or target)
            ]
            features.update({
                "surface_temp_c": lst,
                "surface_temp_z": robust_z(lst, prior_lst, min_samples=3),
                "landsat_ndvi": _num(landsat_current.get("ndvi")),
                "landsat_ndmi": _num(landsat_current.get("ndmi")),
            })

        rain_features, rain_coverage = _rain_features(gpm, target, windows)
        features.update(rain_features)

        era5_features, era5_current = _era5_features(era5, target, profile)
        features.update(era5_features)

        smap_features, smap_current = _smap_features(smap, target)
        features.update(smap_features)

        et_features, et_current = _modis_et_features(modis_et, target)
        features.update(et_features)

        veg_features, veg_current = _modis_veg_features(modis_veg, target)
        features.update(veg_features)

        forecast_features, forecast_current = _forecast_features(forecast, target)
        features.update(forecast_features)

        terrain = _static_for_h3(bundle.get("terrain") or [], h3_index)
        if terrain:
            for key in ["mean_elevation_m", "min_elevation_m", "max_elevation_m", "mean_slope_deg", "max_slope_deg", "mean_aspect_deg"]:
                features[key] = _num(terrain.get(key))

        landcover = _static_for_h3(bundle.get("landcover") or [], h3_index)
        if landcover:
            for key in [
                "dominant_class", "dominant_fraction", "tree_cover_fraction", "shrubland_fraction",
                "grassland_fraction", "cropland_fraction", "built_fraction", "bare_sparse_fraction",
                "snow_ice_fraction", "permanent_water_fraction", "herbaceous_wetland_fraction",
                "mangrove_fraction", "moss_lichen_fraction",
            ]:
                features[key] = _num(landcover.get(key))

        jrc = _static_for_h3(bundle.get("jrc_water") or [], h3_index)
        if jrc:
            features.update({
                "water_occurrence_pct": _num(jrc.get("water_occurrence_pct")),
                "water_recurrence_pct": _num(jrc.get("water_recurrence_pct")),
                "water_seasonality_months": _num(jrc.get("water_seasonality_months")),
                "jrc_permanent_water_fraction": _num(jrc.get("permanent_water_fraction")),
                "historic_extent_fraction": _num(jrc.get("historic_extent_fraction")),
            })

        soil_rows = [row for row in (bundle.get("soilgrids") or []) if int(row.get("h3_index") or -1) == h3_index]
        soil_features, soil_quality = _soil_features(soil_rows, profile)
        features.update(soil_features)

        anchor_valid = _num(anchor.get("valid_fraction")) or 0.0
        s2_current = _nearest_before(
            s2_by_h3.get(h3_index, []), target, date_key="snapshot_date", max_age_days=35
        )
        source_quality = {
            "sentinel2": _source_quality(
                "sentinel2",
                target=target,
                row=s2_current,
                valid_fraction=_num(s2_current.get("valid_fraction")) if s2_current else None,
                date_key="snapshot_date",
            ),
            "sentinel1": _source_quality("sentinel1", target=target, row=s1_current, valid_fraction=_num(s1_current.get("valid_fraction")) if s1_current else None, date_key="snapshot_date"),
            "landsat": _source_quality("landsat", target=target, row=landsat_current, valid_fraction=_num(landsat_current.get("valid_fraction")) if landsat_current else None, date_key="snapshot_date"),
            "gpm": _source_quality("gpm", target=target, row=_nearest_before(gpm, target, date_key="observation_date", max_age_days=2), coverage=rain_coverage, date_key="observation_date"),
            "era5": _source_quality("era5", target=target, row=era5_current, date_key="observation_date"),
            "smap": _source_quality("smap", target=target, row=smap_current, date_key="observed_at"),
            "modis_et": _source_quality("modis_et", target=target, row=et_current, valid_fraction=_num(et_current.get("valid_fraction")) if et_current else None, date_key="period_end"),
            "modis_vegetation": _source_quality("modis_vegetation", target=target, row=veg_current, valid_fraction=_num(veg_current.get("valid_fraction")) if veg_current else None, date_key="period_end"),
            "forecast": _source_quality("forecast", target=target, row=forecast_current, date_key="issued_at"),
            "terrain": _source_quality("terrain", target=target, row=terrain, valid_fraction=_num(terrain.get("valid_fraction")) if terrain else None),
            "landcover": _source_quality("landcover", target=target, row=landcover, valid_fraction=_num(landcover.get("valid_fraction")) if landcover else None),
            "jrc_water": _source_quality("jrc_water", target=target, row=jrc, valid_fraction=_num(jrc.get("valid_fraction")) if jrc else None),
            "soilgrids": clip01(soil_quality),
        }
        source_available = {key: value > 0 for key, value in source_quality.items()}
        confidence = safe_mean([q for q in source_quality.values() if q > 0]) or 0.0

        source_dates = {
            "sentinel2": str(_date(s2_current.get("snapshot_date"))) if s2_current else None,
            "sentinel1": str(_date(s1_current.get("snapshot_date"))) if s1_current else None,
            "landsat": str(_date(landsat_current.get("snapshot_date"))) if landsat_current else None,
            "gpm": str(_date((_nearest_before(gpm, target, date_key="observation_date", max_age_days=2) or {}).get("observation_date"))) if gpm else None,
            "era5": str(_date(era5_current.get("observation_date"))) if era5_current else None,
            "smap": str(_date(smap_current.get("observed_at"))) if smap_current else None,
            "modis_et": str(_date(et_current.get("period_end"))) if et_current else None,
            "modis_vegetation": str(_date(veg_current.get("period_end"))) if veg_current else None,
            "forecast_issue": str(_date(forecast_current.get("issued_at"))) if forecast_current else None,
        }
        source_versions = {
            "sentinel2": _source_version(s2_current),
            "sentinel1": _source_version(s1_current),
            "landsat": _source_version(landsat_current),
            "gpm": _source_version(_nearest_before(gpm, target, date_key="observation_date", max_age_days=2)),
            "era5": _source_version(era5_current),
            "smap": _source_version(smap_current),
            "modis_et": _source_version(et_current),
            "modis_vegetation": _source_version(veg_current),
            "terrain": _source_version(terrain),
            "landcover": _source_version(landcover),
            "jrc_water": _source_version(jrc),
            "soilgrids": _source_version(soil_rows[-1] if soil_rows else None),
        }

        results.append({
            "farm_id": str(farm["farm_id"]),
            "farmer_id": str(farm["farmer_id"]),
            "fpo_id": str(farm["fpo_id"]) if farm.get("fpo_id") else None,
            "h3_index": h3_index,
            "h3_resolution": int(anchor.get("h3_resolution") or farm.get("h3_resolution") or 12),
            "feature_date": target,
            "crop_code": crop_code,
            "crop_profile_version": str(profile["profile_version"]),
            "feature_version": FEATURE_VERSION,
            "anchor_dataset": f"{anchor_dataset}_l2a" if anchor_dataset != "sentinel2" else "sentinel_2_l2a",
            "anchor_scene_id": anchor.get("scene_id"),
            "observed_area_m2": _num(anchor.get("observed_area_m2")),
            "anchor_valid_fraction": anchor_valid,
            "confidence": clip01(confidence),
            "features": features,
            "quality": {
                "source_quality": source_quality,
                "source_available": source_available,
                "anchor_valid_fraction": anchor_valid,
                "rainfall_coverage": rain_coverage,
                "spatial_note": "H3-specific optical/radar/terrain/soil signals plus coarse farm/regional climate context; coarse sources are not H3-resolution observations.",
            },
            "source_dates": source_dates,
            "source_versions": source_versions,
        })

    return results
