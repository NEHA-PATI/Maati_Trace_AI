from __future__ import annotations

from typing import Any
from uuid import UUID

from services.analytics_query_service.app.repository import (
    get_history,
    get_latest_aggregate,
    get_latest_features,
)


def _signal_from_ndvi(value: float | None) -> str | None:
    if value is None:
        return None

    if value >= 0.5:
        return "strong vegetation signal"

    if value >= 0.3:
        return "moderate vegetation signal"

    if value >= 0.15:
        return "weak vegetation signal"

    return "very low vegetation signal"


def _signal_from_ndmi(value: float | None) -> str | None:
    if value is None:
        return None

    if value >= 0.25:
        return "good moisture signal"

    if value >= 0.05:
        return "moderate moisture signal"

    if value >= -0.05:
        return "weak moisture signal"

    return "dryness signal visible"


def _signal_from_bsi(value: float | None) -> str | None:
    if value is None:
        return None

    if value >= 0.15:
        return "high bare soil signal"

    if value >= 0.05:
        return "moderate bare soil signal"

    if value >= -0.05:
        return "neutral bare soil signal"

    return "low bare soil signal"


def _signal_from_cloud(value: float | None) -> str | None:
    if value is None:
        return None

    if value <= 5:
        return "clear usable scene"

    if value <= 20:
        return "mostly usable scene"

    if value <= 40:
        return "partially cloudy scene"

    return "low quality cloudy scene"


def build_latest_response(farm_id: UUID) -> dict[str, Any] | None:
    aggregate = get_latest_aggregate(farm_id)

    if aggregate is None:
        return None

    features = get_latest_features(farm_id)

    aggregate["features"] = features

    return aggregate


def build_history_response(farm_id: UUID, limit: int) -> dict[str, Any]:
    items = get_history(farm_id=farm_id, limit=limit)

    return {
        "farm_id": farm_id,
        "item_count": len(items),
        "items": items,
    }


def build_summary_response(farm_id: UUID) -> dict[str, Any]:
    aggregate = get_latest_aggregate(farm_id)

    if aggregate is None:
        return {
            "farm_id": farm_id,
            "has_analysis": False,
            "latest_snapshot_date": None,
            "latest_scene_id": None,
            "vegetation_signal": None,
            "moisture_signal": None,
            "bare_soil_signal": None,
            "data_quality_signal": None,
            "avg_ndvi": None,
            "avg_ndmi": None,
            "avg_bsi": None,
            "avg_cloud_percentage": None,
        }

    return {
        "farm_id": farm_id,
        "has_analysis": True,
        "latest_snapshot_date": aggregate["snapshot_date"],
        "latest_scene_id": aggregate["scene_id"],
        "vegetation_signal": _signal_from_ndvi(aggregate.get("avg_ndvi")),
        "moisture_signal": _signal_from_ndmi(aggregate.get("avg_ndmi")),
        "bare_soil_signal": _signal_from_bsi(aggregate.get("avg_bsi")),
        "data_quality_signal": _signal_from_cloud(aggregate.get("avg_cloud_percentage")),
        "avg_ndvi": aggregate.get("avg_ndvi"),
        "avg_ndmi": aggregate.get("avg_ndmi"),
        "avg_bsi": aggregate.get("avg_bsi"),
        "avg_cloud_percentage": aggregate.get("avg_cloud_percentage"),
    }