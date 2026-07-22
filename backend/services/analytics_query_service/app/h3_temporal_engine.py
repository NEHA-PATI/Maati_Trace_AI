from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


RULE_VERSION = "h3_temporal_observation_v1"


def _number(value: Any, default: float = 0.0) -> float:
    return default if value is None else float(value)


def _round(value: Any, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def _as_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _freshness(age_days: int) -> str:
    if age_days <= 7:
        return "current"
    if age_days <= 15:
        return "recent"
    if age_days <= 30:
        return "older_but_usable"
    return "historical"


def _confidence(valid_fraction: float, age_days: int) -> str:
    if valid_fraction >= 0.75:
        level = 3
    elif valid_fraction >= 0.50:
        level = 2
    elif valid_fraction >= 0.20:
        level = 1
    else:
        return "unavailable"

    if age_days > 30:
        level -= 1
    elif age_days > 15 and level > 1:
        level -= 1

    return {3: "high", 2: "moderate", 1: "low", 0: "very_low"}[level]


def _canopy(ndvi: float | None) -> str:
    if ndvi is None:
        return "no_valid_observation_yet"
    if ndvi < 0.15:
        return "very_low_green_canopy"
    if ndvi < 0.30:
        return "sparse_or_emerging_canopy"
    if ndvi < 0.50:
        return "moderate_green_canopy"
    return "dense_green_canopy"


def _moisture(ndmi: float | None) -> str:
    if ndmi is None:
        return "not_available"
    if ndmi < -0.10:
        return "strong_dryness_signal"
    if ndmi < 0.05:
        return "low_moisture_signal"
    if ndmi < 0.25:
        return "moderate_moisture_signal"
    return "high_moisture_signal"


def _soil_exposure(bsi: float | None) -> str:
    if bsi is None:
        return "not_available"
    if bsi >= 0.15:
        return "high_bare_soil_signal"
    if bsi >= 0.05:
        return "moderate_bare_soil_signal"
    return "low_bare_soil_signal"


def _change(current: float | None, previous: float | None) -> tuple[float | None, str]:
    if current is None or previous is None:
        return None, "baseline_not_available"
    delta = round(current - previous, 6)
    if delta <= -0.10:
        return delta, "strong_decrease"
    if delta <= -0.04:
        return delta, "decrease"
    if delta < 0.04:
        return delta, "stable"
    if delta < 0.10:
        return delta, "increase"
    return delta, "strong_increase"


def _priority(
    canopy: str,
    moisture: str,
    ndvi_change: str,
    confidence: str,
) -> str:
    if confidence in {"unavailable", "very_low"}:
        return "watch"
    if ndvi_change == "strong_decrease" and moisture in {
        "strong_dryness_signal",
        "low_moisture_signal",
    }:
        return "inspect_first"
    if ndvi_change in {"strong_decrease", "decrease"}:
        return "inspect"
    if canopy == "very_low_green_canopy":
        return "watch"
    return "normal_monitoring"


def build_h3_observation(
    row: dict[str, Any],
    *,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    today = as_of_date or datetime.now(timezone.utc).date()
    observed_on = _as_date(row.get("snapshot_date"))
    previous_on = _as_date(row.get("previous_snapshot_date"))
    age_days = max(0, (today - observed_on).days) if observed_on else 0
    valid_fraction = _number(row.get("valid_fraction"))

    ndvi = _round(row.get("ndvi"))
    ndmi = _round(row.get("ndmi"))
    bsi = _round(row.get("bsi"))
    canopy = _canopy(ndvi)
    moisture = _moisture(ndmi)
    soil = _soil_exposure(bsi)
    ndvi_delta, ndvi_change = _change(ndvi, _round(row.get("previous_ndvi")))
    ndmi_delta, ndmi_change = _change(ndmi, _round(row.get("previous_ndmi")))
    confidence = _confidence(valid_fraction, age_days)

    observed_area = _number(row.get("observed_area_m2"))
    water_area = _number(row.get("water_area_m2"))
    water_fraction = water_area / observed_area if observed_area > 0 else 0.0

    return {
        "h3_index": int(row["h3_index"]),
        "h3_resolution": int(row.get("h3_resolution") or 12),
        "data_status": "latest_valid_historical_observation",
        "observation_date": observed_on,
        "observation_age_days": age_days,
        "freshness_status": _freshness(age_days),
        "confidence_level": confidence,
        "valid_fraction": round(valid_fraction, 6),
        "valid_coverage_percent": round(valid_fraction * 100.0, 2),
        "scene_id": row.get("scene_id"),
        "processing_version": row.get("processing_version"),
        "ndvi": ndvi,
        "ndmi": ndmi,
        "bsi": bsi,
        "fvc_proxy": _round(row.get("fvc_proxy")),
        "nirv": _round(row.get("nirv")),
        "canopy_condition": canopy,
        "moisture_condition": moisture,
        "soil_exposure_condition": soil,
        "surface_water_signal": (
            "present" if water_fraction >= 0.05 else "not_detected"
        ),
        "previous_observation_date": previous_on,
        "observation_interval_days": (
            (observed_on - previous_on).days
            if observed_on and previous_on
            else None
        ),
        "ndvi_change": ndvi_delta,
        "ndvi_trend": ndvi_change,
        "ndmi_change": ndmi_delta,
        "moisture_trend": ndmi_change,
        "action_priority": _priority(
            canopy,
            moisture,
            ndvi_change,
            confidence,
        ),
    }


def build_missing_h3_observation(h3_index: int) -> dict[str, Any]:
    return {
        "h3_index": int(h3_index),
        "h3_resolution": 12,
        "data_status": "awaiting_first_valid_observation",
        "observation_date": None,
        "observation_age_days": None,
        "freshness_status": "not_available",
        "confidence_level": "unavailable",
        "valid_fraction": 0.0,
        "valid_coverage_percent": 0.0,
        "scene_id": None,
        "processing_version": None,
        "ndvi": None,
        "ndmi": None,
        "bsi": None,
        "fvc_proxy": None,
        "nirv": None,
        "canopy_condition": "waiting_for_clear_satellite_view",
        "moisture_condition": "waiting_for_clear_satellite_view",
        "soil_exposure_condition": "waiting_for_clear_satellite_view",
        "surface_water_signal": "not_available",
        "previous_observation_date": None,
        "observation_interval_days": None,
        "ndvi_change": None,
        "ndvi_trend": "baseline_not_available",
        "ndmi_change": None,
        "moisture_trend": "baseline_not_available",
        "action_priority": "awaiting_observation",
    }