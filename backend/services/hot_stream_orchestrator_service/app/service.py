from __future__ import annotations

from typing import Any
from uuid import UUID

from services.hot_stream_orchestrator_service.app.clients import (
    get_farm,
    run_raster_preview_from_search,
    write_sentinel2_to_lakehouse,
)
from services.hot_stream_orchestrator_service.app.schemas import (
    FarmAnalysisMaterializeRequest,
)


class HotStreamOrchestratorError(RuntimeError):
    pass


def _make_tiny_bbox_from_farm_bbox(
    farm_bbox: list[float],
    size_deg: float,
) -> list[float]:
    min_lon, min_lat, max_lon, max_lat = farm_bbox

    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0

    half = size_deg / 2.0

    return [
        center_lon - half,
        center_lat - half,
        center_lon + half,
        center_lat + half,
    ]


def _choose_analysis_bbox(
    farm: dict[str, Any],
    payload: FarmAnalysisMaterializeRequest,
) -> list[float]:
    farm_bbox = farm.get("bbox")

    if not farm_bbox or len(farm_bbox) != 4:
        raise HotStreamOrchestratorError("Farm does not have a valid bbox")

    if payload.use_tiny_preview_bbox:
        return _make_tiny_bbox_from_farm_bbox(
            farm_bbox=farm_bbox,
            size_deg=payload.tiny_bbox_size_deg,
        )

    return farm_bbox


def materialize_farm_analysis(
    farm_id: UUID,
    payload: FarmAnalysisMaterializeRequest,
) -> dict[str, Any]:
    farm = get_farm(farm_id)

    analysis_bbox = _choose_analysis_bbox(farm, payload)

    raster_result = run_raster_preview_from_search(
        farm_id=farm_id,
        bbox=analysis_bbox,
        provider=payload.provider,
        collection_id=payload.collection_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        max_cloud_cover=payload.max_cloud_cover,
        h3_resolution=payload.h3_resolution,
    )

    if not raster_result.get("features"):
        raise HotStreamOrchestratorError(
            "Raster processor returned no feature rows"
        )

    lakehouse_result = write_sentinel2_to_lakehouse(
        farm_id=farm_id,
        raster_result=raster_result,
    )

    return {
        "farm": farm,
        "analysis_bbox": analysis_bbox,
        "raster_result": raster_result,
        "lakehouse_result": lakehouse_result,
    }