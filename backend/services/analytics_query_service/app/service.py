from __future__ import annotations

from typing import Any
from uuid import UUID

from services.analytics_query_service.app.repository import (
    get_farm_grid_cells,
    get_history,
    get_latest_aggregate,
    get_latest_features,
    get_farm_h3_cells,
)
from services.farm_registry_service.app.repository import get_farm


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
    farm = get_farm(farm_id)
    farm_h3_cells = get_farm_h3_cells(farm_id)
    total_farm_h3_cells = int(farm.get("h3_cell_count") or len(farm.get("h3_cells") or []) or len(farm_h3_cells) or 0) if farm else len(farm_h3_cells)

    if aggregate is None:
        grid_cells = get_farm_grid_cells(farm_id)
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
            "weighted_ndvi": None,
            "weighted_ndmi": None,
            "weighted_ndwi": None,
            "weighted_bsi": None,
            "weighted_evi": None,
            "weighted_savi": None,
            "weighted_msi": None,
            "weighted_nbr": None,
            "weighted_ndre": None,
            "weighted_surface_temp_c": None,
            "valid_pixel_percentage": None,
            "total_h3_cells": total_farm_h3_cells,
            "total_farm_h3_cells": total_farm_h3_cells,
            "processed_h3_cells": 0,
            "latest_processed_h3_cells": 0,
            "total_grid_cells": len(grid_cells),
            "grid_cells_with_values": 0,
        }

    features = get_latest_features(farm_id)
    valid_weights = [max(1.0, float(item.get("valid_pixel_count") or item.get("pixel_count") or 0)) for item in features]
    weight_sum = sum(valid_weights) or 1.0

    def wavg(field: str) -> float | None:
        values = [item.get(field) for item in features if item.get(field) is not None]
        if not values:
            return None
        return round(sum(float(item.get(field) or 0) * valid_weights[index] for index, item in enumerate(features) if item.get(field) is not None) / weight_sum, 6)

    surface_temp = None
    if features:
        surface_temp = round(sum((float(item.get("mean_swir16") or 0) + float(item.get("mean_swir22") or 0)) / 2.0 * valid_weights[index] for index, item in enumerate(features)) / weight_sum, 6)

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
        "weighted_ndvi": wavg("ndvi"),
        "weighted_ndmi": wavg("ndmi"),
        "weighted_ndwi": wavg("ndwi"),
        "weighted_bsi": wavg("bsi"),
        "weighted_evi": wavg("evi"),
        "weighted_savi": wavg("savi"),
        "weighted_msi": wavg("msi"),
        "weighted_nbr": wavg("nbr"),
        "weighted_ndre": wavg("ndre"),
        "weighted_surface_temp_c": surface_temp,
        "valid_pixel_percentage": round(sum(float(item.get("valid_pixel_count") or 0) for item in features) / max(1.0, sum(float(item.get("pixel_count") or 0) for item in features)) * 100.0, 6) if features else None,
        "total_h3_cells": total_farm_h3_cells,
        "total_farm_h3_cells": total_farm_h3_cells,
        "processed_h3_cells": len({item.get("h3_index") for item in features if item.get("h3_index") is not None}),
        "latest_processed_h3_cells": len({item.get("h3_index") for item in features if item.get("h3_index") is not None}),
        "total_grid_cells": len(get_farm_grid_cells(farm_id)),
        "grid_cells_with_values": len(get_farm_grid_cells(farm_id)),
    }
