from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.analytics_query_service.app.feature_engine.math_utils import (
    absolute_z_anomaly,
    clip01,
    finite_number,
    high_z_stress,
    low_z_stress,
    normalize_high,
    safe_mean,
    trapezoid_suitability,
)


@dataclass(frozen=True)
class ComponentResult:
    value: float | None
    quality: float
    details: dict[str, Any]


SOURCE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "canopy_moisture_stress": ("sentinel2",),
    "canopy_moisture_condition": ("sentinel2",),
    "rootzone_moisture_stress": ("smap", "era5"),
    "rootzone_moisture_condition": ("smap", "era5"),
    "rainfall_stress": ("gpm",),
    "thermal_stress": ("landsat", "era5"),
    "lst_stress": ("landsat",),
    "air_temperature_stress": ("era5",),
    "et_deficit_stress": ("modis_et",),
    "atmospheric_demand_stress": ("forecast",),
    "et0_stress": ("forecast",),
    "sar_anomaly": ("sentinel1",),
    "sar_condition": ("sentinel1",),
    "vegetation_condition": ("sentinel2", "modis_vegetation"),
    "growth_trend_condition": ("sentinel2", "modis_vegetation"),
    "growth_trajectory_condition": ("sentinel2",),
    "moisture_support_condition": ("sentinel2", "smap", "era5"),
    "climate_support_condition": ("gpm", "landsat", "era5"),
    "temporal_anomaly": ("sentinel2", "modis_vegetation"),
    "spatial_anomaly": ("sentinel2",),
    "environmental_stress_evidence": ("sentinel2", "gpm", "landsat", "smap", "era5"),
    "growth_trajectory_anomaly": ("sentinel2",),
    "optical_water_signal": ("sentinel2",),
    "wet_soil_signal": ("smap", "era5"),
    "rain_excess": ("gpm",),
    "ponding_terrain": ("terrain",),
    "historic_water_context": ("jrc_water",),
    "soil_ph_suitability": ("soilgrids",),
    "soil_soc_suitability": ("soilgrids",),
    "soil_cec_suitability": ("soilgrids",),
    "soil_bulk_density_suitability": ("soilgrids",),
    "soil_texture_suitability": ("soilgrids",),
    "drainage_suitability": ("terrain", "jrc_water"),
    "optical_nutrient_stress": ("sentinel2",),
    "soil_nutrient_stress": ("soilgrids",),
    "growth_nutrient_stress": ("sentinel2",),
    "terrain_erosion_risk": ("terrain",),
    "bare_exposure": ("sentinel2", "landcover"),
    "rain_erosivity_proxy": ("gpm",),
    "soil_erodibility_proxy": ("soilgrids",),
}


def _source_quality(quality: dict[str, Any], sources: tuple[str, ...]) -> float:
    source_quality = quality.get("source_quality") or {}
    values = []
    for name in sources:
        raw = finite_number(source_quality.get(name))
        if raw is not None and raw > 0:
            values.append(clip01(raw))
    if not values:
        return 0.0
    # A component can still be computed from a subset of its optional sources.
    return sum(values) / len(sources)


def _result(value: float | None, quality: dict[str, Any], key: str, details: dict[str, Any] | None = None) -> ComponentResult:
    return ComponentResult(
        value=None if value is None else clip01(value),
        quality=_source_quality(quality, SOURCE_REQUIREMENTS.get(key, ())),
        details=details or {},
    )


def _mean_available(values: list[float | None]) -> float | None:
    return safe_mean([v for v in values if v is not None])


def _condition_from_low_z(features: dict[str, Any], keys: list[str], critical: float) -> float | None:
    risks = [low_z_stress(features.get(key), critical) for key in keys]
    value = _mean_available(risks)
    return None if value is None else 1.0 - value


def _profile_norm(profile: dict[str, Any], key: str, default: float) -> float:
    return float((profile.get("normalization") or {}).get(key, default))


def _soil_range(profile: dict[str, Any], key: str):
    return (profile.get("soil_ranges") or {}).get(key)


def _texture_score(features: dict[str, Any], profile: dict[str, Any]) -> float | None:
    scores = []
    for feature_key, profile_key in [
        ("soil_clay", "clay"),
        ("soil_sand", "sand"),
        ("soil_silt", "silt"),
    ]:
        bounds = _soil_range(profile, profile_key)
        if bounds:
            score = trapezoid_suitability(features.get(feature_key), bounds)
            if score is not None:
                scores.append(score)
    return safe_mean(scores)


def compute_component(
    component_key: str,
    *,
    features: dict[str, Any],
    quality: dict[str, Any],
    profile: dict[str, Any],
    formula_parameters: dict[str, Any] | None = None,
) -> ComponentResult:
    params = formula_parameters or {}
    critical = float((profile.get("normalization") or {}).get("z_critical", 3.0))

    if component_key == "canopy_moisture_stress":
        ndmi = low_z_stress(features.get("ndmi_z"), critical)
        msi = high_z_stress(features.get("msi_z"), critical)
        value = safe_mean([ndmi, msi]) if ndmi is None or msi is None else 0.65 * ndmi + 0.35 * msi
        return _result(value, quality, component_key, {"ndmi_stress": ndmi, "msi_stress": msi})

    if component_key == "canopy_moisture_condition":
        base = compute_component("canopy_moisture_stress", features=features, quality=quality, profile=profile, formula_parameters=params)
        return ComponentResult(None if base.value is None else 1.0 - base.value, base.quality, base.details)

    if component_key == "rootzone_moisture_stress":
        smap = low_z_stress(features.get("smap_rootzone_z"), critical)
        era5 = low_z_stress(features.get("era5_rootzone_z"), critical)
        if smap is not None and era5 is not None:
            value = 0.55 * smap + 0.45 * era5
        else:
            value = safe_mean([smap, era5])
        return _result(value, quality, component_key, {"smap": smap, "era5": era5})

    if component_key == "rootzone_moisture_condition":
        base = compute_component("rootzone_moisture_stress", features=features, quality=quality, profile=profile, formula_parameters=params)
        return ComponentResult(None if base.value is None else 1.0 - base.value, base.quality, base.details)

    if component_key == "rainfall_stress":
        days = int(params.get("rain_window_days") or (profile.get("temporal_windows") or {}).get("primary_rainfall_window") or 30)
        z = low_z_stress(features.get(f"rain_{days}d_z"), critical)
        deficit = finite_number(features.get(f"rain_{days}d_deficit"))
        if z is not None and deficit is not None:
            value = 0.60 * z + 0.40 * clip01(deficit)
        else:
            value = safe_mean([z, deficit])
        return _result(value, quality, component_key, {"window_days": days, "z_stress": z, "deficit": deficit})

    if component_key == "thermal_stress":
        lst = high_z_stress(features.get("surface_temp_z"), critical)
        skin = high_z_stress(features.get("era5_skin_temp_z"), critical)
        if lst is not None and skin is not None:
            value = 0.70 * lst + 0.30 * skin
        else:
            value = safe_mean([lst, skin])
        return _result(value, quality, component_key, {"lst": lst, "skin": skin})

    if component_key == "lst_stress":
        return _result(high_z_stress(features.get("surface_temp_z"), critical), quality, component_key)

    if component_key == "air_temperature_stress":
        return _result(high_z_stress(features.get("era5_temp_max_z"), critical), quality, component_key)

    if component_key == "et_deficit_stress":
        ratio = finite_number(features.get("et_pet_ratio"))
        return _result(None if ratio is None else clip01(1.0 - ratio), quality, component_key, {"et_pet_ratio": ratio})

    if component_key == "atmospheric_demand_stress":
        value = normalize_high(
            features.get("forecast_vpd"),
            _profile_norm(profile, "vpd_low", 0.8),
            _profile_norm(profile, "vpd_high", 2.8),
        )
        return _result(value, quality, component_key)

    if component_key == "et0_stress":
        value = normalize_high(
            features.get("forecast_et0_mm"),
            _profile_norm(profile, "et0_low", 3.0),
            _profile_norm(profile, "et0_high", 8.0),
        )
        return _result(value, quality, component_key)

    if component_key in {"sar_anomaly", "sar_condition"}:
        anomaly = absolute_z_anomaly(features.get("sar_ratio_z"), critical)
        if component_key == "sar_condition" and anomaly is not None:
            anomaly = 1.0 - anomaly
        return _result(anomaly, quality, component_key)

    if component_key == "vegetation_condition":
        value = _condition_from_low_z(features, ["ndvi_z", "evi_z", "nirv_z", "lai_z"], critical)
        return _result(value, quality, component_key)

    if component_key == "growth_trend_condition":
        decline_scale = _profile_norm(profile, "slope_decline_scale", 0.01)
        conditions = []
        for key in ["ndvi_slope", "evi_slope", "nirv_slope", "lai_slope"]:
            slope = finite_number(features.get(key))
            if slope is None:
                continue
            conditions.append(1.0 if slope >= 0 else clip01(1.0 + slope / max(1e-6, decline_scale)))
        return _result(safe_mean(conditions), quality, component_key)

    if component_key in {"growth_trajectory_condition", "growth_trajectory_anomaly"}:
        deviation = finite_number(features.get("ndvi_trajectory_deviation"))
        threshold = _profile_norm(profile, "trajectory_critical", 0.30)
        anomaly = None if deviation is None else clip01(abs(deviation) / max(1e-6, threshold))
        value = (1.0 - anomaly) if component_key == "growth_trajectory_condition" and anomaly is not None else anomaly
        return _result(value, quality, component_key, {"deviation": deviation})

    if component_key == "moisture_support_condition":
        canopy = compute_component("canopy_moisture_condition", features=features, quality=quality, profile=profile, formula_parameters=params).value
        root = compute_component("rootzone_moisture_condition", features=features, quality=quality, profile=profile, formula_parameters=params).value
        return _result(safe_mean([canopy, root]), quality, component_key)

    if component_key == "climate_support_condition":
        rain = compute_component("rainfall_stress", features=features, quality=quality, profile=profile, formula_parameters=params).value
        thermal = compute_component("thermal_stress", features=features, quality=quality, profile=profile, formula_parameters=params).value
        risks = safe_mean([rain, thermal])
        return _result(None if risks is None else 1.0 - risks, quality, component_key)

    if component_key == "temporal_anomaly":
        values = [absolute_z_anomaly(features.get(key), critical) for key in ["ndvi_z", "evi_z", "nirv_z", "ndmi_z", "ndre_z", "lai_z"]]
        return _result(safe_mean(values), quality, component_key)

    if component_key == "spatial_anomaly":
        values = [absolute_z_anomaly(features.get(key), critical) for key in ["spatial_ndvi_z", "spatial_ndmi_z", "spatial_nirv_z"]]
        return _result(safe_mean(values), quality, component_key)

    if component_key == "environmental_stress_evidence":
        vals = [
            compute_component("canopy_moisture_stress", features=features, quality=quality, profile=profile, formula_parameters=params).value,
            compute_component("rootzone_moisture_stress", features=features, quality=quality, profile=profile, formula_parameters=params).value,
            compute_component("rainfall_stress", features=features, quality=quality, profile=profile, formula_parameters=params).value,
            compute_component("thermal_stress", features=features, quality=quality, profile=profile, formula_parameters=params).value,
        ]
        return _result(safe_mean(vals), quality, component_key)

    if component_key == "optical_water_signal":
        return _result(safe_mean([high_z_stress(features.get("mndwi_z"), critical), high_z_stress(features.get("ndwi_z"), critical)]), quality, component_key)

    if component_key == "wet_soil_signal":
        return _result(safe_mean([high_z_stress(features.get("smap_rootzone_z"), critical), high_z_stress(features.get("era5_rootzone_z"), critical)]), quality, component_key)

    if component_key == "rain_excess":
        days = int(params.get("rain_window_days") or (profile.get("temporal_windows") or {}).get("primary_rainfall_window") or 30)
        return _result(high_z_stress(features.get(f"rain_{days}d_z"), critical), quality, component_key, {"window_days": days})

    if component_key == "ponding_terrain":
        slope = finite_number(features.get("mean_slope_deg"))
        high = normalize_high(slope, _profile_norm(profile, "ponding_slope_low", 0.2), _profile_norm(profile, "ponding_slope_high", 4.0))
        return _result(None if high is None else 1.0 - high, quality, component_key)

    if component_key == "historic_water_context":
        occurrence = finite_number(features.get("water_occurrence_pct"))
        permanent = finite_number(features.get("jrc_permanent_water_fraction"))
        occurrence_norm = None if occurrence is None else clip01(occurrence / 100.0)
        permanent_norm = None if permanent is None else clip01(permanent)
        if occurrence_norm is not None and permanent_norm is not None:
            value = 0.6 * occurrence_norm + 0.4 * permanent_norm
        else:
            value = safe_mean([occurrence_norm, permanent_norm])
        return _result(value, quality, component_key)

    if component_key == "soil_ph_suitability":
        return _result(trapezoid_suitability(features.get("soil_phh2o"), _soil_range(profile, "phh2o") or []), quality, component_key)

    if component_key == "soil_soc_suitability":
        return _result(normalize_high(features.get("soil_soc"), _profile_norm(profile, "soc_low", 5.0), _profile_norm(profile, "soc_good", 20.0)), quality, component_key)

    if component_key == "soil_cec_suitability":
        return _result(normalize_high(features.get("soil_cec"), _profile_norm(profile, "cec_low", 5.0), _profile_norm(profile, "cec_good", 25.0)), quality, component_key)

    if component_key == "soil_bulk_density_suitability":
        return _result(trapezoid_suitability(features.get("soil_bdod"), _soil_range(profile, "bdod") or []), quality, component_key)

    if component_key == "soil_texture_suitability":
        return _result(_texture_score(features, profile), quality, component_key)

    if component_key == "drainage_suitability":
        slope = finite_number(features.get("mean_slope_deg"))
        occurrence = finite_number(features.get("water_occurrence_pct"))
        mode = str((profile.get("normalization") or {}).get("drainage_mode", "well_drained"))
        water_risk = None if occurrence is None else clip01(occurrence / 100.0)
        if mode == "retain_water":
            slope_condition = None if slope is None else 1.0 - (normalize_high(slope, 1.0, 6.0) or 0.0)
            water_condition = None if water_risk is None else clip01(1.0 - abs(water_risk - 0.20))
        else:
            ponding = compute_component("ponding_terrain", features=features, quality=quality, profile=profile, formula_parameters=params).value
            slope_condition = None if ponding is None else 1.0 - ponding
            water_condition = None if water_risk is None else 1.0 - water_risk
        return _result(safe_mean([slope_condition, water_condition]), quality, component_key)

    if component_key == "optical_nutrient_stress":
        vals = [low_z_stress(features.get(key), critical) for key in ["ndre_z", "reci_z", "gndvi_z"]]
        weighted = None
        if all(v is not None for v in vals):
            weighted = 0.40 * vals[0] + 0.35 * vals[1] + 0.25 * vals[2]
        else:
            weighted = safe_mean(vals)
        return _result(weighted, quality, component_key)

    if component_key == "soil_nutrient_stress":
        nitrogen_support = normalize_high(features.get("soil_nitrogen"), _profile_norm(profile, "nitrogen_low", 0.3), _profile_norm(profile, "nitrogen_good", 1.5))
        soc = compute_component("soil_soc_suitability", features=features, quality=quality, profile=profile, formula_parameters=params).value
        cec = compute_component("soil_cec_suitability", features=features, quality=quality, profile=profile, formula_parameters=params).value
        ph = compute_component("soil_ph_suitability", features=features, quality=quality, profile=profile, formula_parameters=params).value
        supports = [nitrogen_support, soc, cec, ph]
        available = [v for v in supports if v is not None]
        if not available:
            value = None
        elif len(available) == 4:
            value = 0.40 * (1.0 - nitrogen_support) + 0.25 * (1.0 - soc) + 0.20 * (1.0 - cec) + 0.15 * (1.0 - ph)
        else:
            value = 1.0 - safe_mean(available)
        return _result(value, quality, component_key)

    if component_key == "growth_nutrient_stress":
        vals = [low_z_stress(features.get("nirv_z"), critical), low_z_stress(features.get("evi_z"), critical)]
        if vals[0] is not None and vals[1] is not None:
            value = 0.60 * vals[0] + 0.40 * vals[1]
        else:
            value = safe_mean(vals)
        return _result(value, quality, component_key)

    if component_key == "terrain_erosion_risk":
        value = normalize_high(features.get("mean_slope_deg"), _profile_norm(profile, "erosion_slope_low", 2.0), _profile_norm(profile, "erosion_slope_high", 20.0))
        return _result(value, quality, component_key)

    if component_key == "bare_exposure":
        bsi = high_z_stress(features.get("bsi_z"), critical)
        fvc = finite_number(features.get("fvc_proxy"))
        bare = finite_number(features.get("bare_sparse_fraction"))
        fvc_risk = None if fvc is None else clip01(1.0 - fvc)
        bare_risk = None if bare is None else clip01(bare)
        vals = [bsi, fvc_risk, bare_risk]
        if all(v is not None for v in vals):
            value = 0.50 * bsi + 0.30 * fvc_risk + 0.20 * bare_risk
        else:
            value = safe_mean(vals)
        return _result(value, quality, component_key)

    if component_key == "rain_erosivity_proxy":
        return _result(high_z_stress(features.get("rain_7d_z"), critical), quality, component_key)

    if component_key == "soil_erodibility_proxy":
        silt = finite_number(features.get("soil_silt"))
        sand = finite_number(features.get("soil_sand"))
        soc_support = compute_component("soil_soc_suitability", features=features, quality=quality, profile=profile, formula_parameters=params).value
        silt_risk = None if silt is None else clip01(silt / 70.0)
        sand_risk = None if sand is None else clip01(sand / 85.0)
        soc_risk = None if soc_support is None else 1.0 - soc_support
        if silt_risk is not None and sand_risk is not None and soc_risk is not None:
            value = 0.45 * silt_risk + 0.25 * sand_risk + 0.30 * soc_risk
        else:
            value = safe_mean([silt_risk, sand_risk, soc_risk])
        return _result(value, quality, component_key, {"note": "relative proxy, not laboratory/RUSLE K factor"})

    raise KeyError(f"Unknown formula component: {component_key}")
