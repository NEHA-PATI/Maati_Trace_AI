from __future__ import annotations

import json
from datetime import date
from typing import Any
from uuid import UUID

from shapely.geometry import shape

from services.farm_registry_service.app.area_calculator import calculate_area_acres, validate_farm_polygon
from services.farm_registry_service.app.external_clients import (
    ExternalServiceError,
    create_h3_preview,
    validate_location,
)
from services.farm_registry_service.app.repository import get_farm_for_repair, update_farm_derived_fields
from services.hot_stream_orchestrator_service.app.clients import (
    OrchestratorClientError,
    get_farm,
    run_raster_preview_from_search,
    write_sentinel2_to_lakehouse,
)
from services.hot_stream_orchestrator_service.app.schemas import FarmAnalysisMaterializeRequest


class HotStreamOrchestratorError(RuntimeError):
    def __init__(self, message: str, code: str = "HOT_STREAM_ERROR", status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


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


def _normalize_bbox(raw_bbox: Any) -> list[float] | None:
    if raw_bbox is None:
        return None
    if isinstance(raw_bbox, str):
        try:
            raw_bbox = json.loads(raw_bbox)
        except Exception:
            return None
    if isinstance(raw_bbox, (list, tuple)) and len(raw_bbox) == 4:
        try:
            bbox = [float(raw_bbox[0]), float(raw_bbox[1]), float(raw_bbox[2]), float(raw_bbox[3])]
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                return None
            if bbox[0] < -180 or bbox[2] > 180 or bbox[1] < -90 or bbox[3] > 90:
                return None
            return bbox
        except Exception:
            return None
    return None


def _normalize_polygon(geojson: Any) -> dict[str, Any] | None:
    if geojson is None:
        return None
    if isinstance(geojson, str):
        try:
            geojson = json.loads(geojson)
        except Exception:
            return None
    if not isinstance(geojson, dict):
        return None
    if geojson.get("type") not in {"Polygon", "MultiPolygon"}:
        return None
    return geojson


def _polygon_bbox_from_geojson(polygon_geojson: dict[str, Any]) -> list[float] | None:
    try:
        geom = shape(polygon_geojson)
        minx, miny, maxx, maxy = geom.bounds
        return [float(minx), float(miny), float(maxx), float(maxy)]
    except Exception:
        return None


def _choose_analysis_bbox(
    farm: dict[str, Any],
    payload: FarmAnalysisMaterializeRequest,
) -> list[float]:
    farm_bbox = _normalize_bbox(farm.get("bbox"))

    if farm_bbox is None:
        farm_bbox = _polygon_bbox_from_geojson(_normalize_polygon(farm.get("polygon_geojson")) or {})

    if not farm_bbox or len(farm_bbox) != 4:
        raise HotStreamOrchestratorError("Farm does not have a valid bbox or polygon geometry", code="FARM_GEOMETRY_INVALID", status_code=422)

    if payload.use_tiny_preview_bbox:
        return _make_tiny_bbox_from_farm_bbox(
            farm_bbox=farm_bbox,
            size_deg=payload.tiny_bbox_size_deg,
        )

    return farm_bbox


def ensure_farm_analysis_ready(farm_id: UUID) -> dict[str, Any]:
    farm = get_farm_for_repair(farm_id)
    if farm is None:
        raise HotStreamOrchestratorError("Farm not found", code="FARM_NOT_FOUND", status_code=404)

    if not farm.get("farmer_id"):
        raise HotStreamOrchestratorError(
            "This farm is missing farmer linkage. Please link it before analysis.",
            code="FARM_OWNER_MISSING",
            status_code=422,
        )

    polygon = _normalize_polygon(farm.get("polygon_geojson"))
    if polygon is None:
        raise HotStreamOrchestratorError(
            "Farm polygon is missing or invalid.",
            code="FARM_POLYGON_INVALID",
            status_code=422,
        )

    try:
        validate_farm_polygon(polygon)
    except Exception as exc:
        raise HotStreamOrchestratorError(str(exc), code="FARM_POLYGON_INVALID", status_code=422) from exc

    warnings: list[str] = []
    repaired_fields: list[str] = []

    existing_bbox = _normalize_bbox(farm.get("bbox"))
    computed_bbox = _polygon_bbox_from_geojson(polygon)
    bbox = existing_bbox or computed_bbox
    if bbox and existing_bbox != bbox:
        repaired_fields.append("bbox")
    if bbox is None:
        raise HotStreamOrchestratorError(
            "Farm bounding box could not be derived from geometry.",
            code="FARM_GEOMETRY_INVALID",
            status_code=422,
        )

    area_acres = farm.get("area_acres")
    if area_acres is None or float(area_acres or 0) <= 0:
        try:
            area_acres = calculate_area_acres(polygon)
            repaired_fields.append("area_acres")
        except Exception as exc:
            warnings.append(f"Area calculation failed: {exc}")
            area_acres = None

    h3_resolution = int(farm.get("h3_resolution") or 12)

    try:
        preview = create_h3_preview(polygon=polygon, resolution=h3_resolution, max_cells=None)
    except ExternalServiceError as exc:
        raise HotStreamOrchestratorError(
            f"H3 preview failed: {exc}",
            code="H3_PREVIEW_ERROR",
            status_code=422,
        ) from exc
    h3_cells = preview.get("h3_cells_bigint") or []
    h3_cell_count = int(preview.get("cell_count") or len(h3_cells) or 0)

    if h3_cells or h3_cell_count:
        if not farm.get("h3_cells") or int(farm.get("h3_cell_count") or 0) != int(h3_cell_count):
            repaired_fields.append("h3_cells_bigint")
            repaired_fields.append("h3_cell_count")
    else:
        warnings.append("H3 preview returned no cells.")

    location_updates: dict[str, Any] = {}
    if farm.get("district_name") and (not farm.get("district_code") or not farm.get("block_code") or not farm.get("block_name")):
        try:
            location = validate_location(
                state_name=farm.get("state_name") or "Odisha",
                district_name=farm["district_name"],
                block_name=farm.get("block_name"),
                block_code=farm.get("block_code"),
            )
            location_updates = {
                "district_code": location.get("district_code"),
                "block_code": location.get("block_code"),
            }
            repaired_fields.extend([key for key, value in location_updates.items() if value is not None])
        except ExternalServiceError as exc:
            warnings.append(f"Location validation skipped: {exc}")
        except Exception as exc:
            warnings.append(f"Location validation skipped: {exc}")

    updated = update_farm_derived_fields(
        farm_id,
        district_code=location_updates.get("district_code"),
        block_code=location_updates.get("block_code"),
        h3_resolution=h3_resolution,
        h3_cells=h3_cells if h3_cells else None,
        h3_cell_count=h3_cell_count if h3_cells else None,
        area_acres=area_acres if area_acres is not None else None,
        bbox=bbox,
    )

    if updated is not None:
        farm = updated
        farm["h3_cells"] = h3_cells

    return {
        "farm": farm,
        "repaired_fields": repaired_fields,
        "warnings": warnings,
        "h3_cell_count": h3_cell_count,
        "bbox": bbox,
        "area_acres": area_acres,
        "preview": preview,
    }


def materialize_farm_analysis(
    farm_id: UUID,
    payload: FarmAnalysisMaterializeRequest,
) -> dict[str, Any]:
    repair_result = ensure_farm_analysis_ready(farm_id)
    farm = repair_result["farm"]

    analysis_bbox = _choose_analysis_bbox(farm, payload)

    try:
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
    except OrchestratorClientError as exc:
        message = str(exc)
        if "No Sentinel-2 scene found" not in message:
            raise

        farm_bbox = _normalize_bbox(farm.get("bbox")) or _polygon_bbox_from_geojson(_normalize_polygon(farm.get("polygon_geojson")) or {})
        if not farm_bbox:
            raise

        fallback_end = date.today().isoformat()
        raster_result = run_raster_preview_from_search(
            farm_id=farm_id,
            bbox=farm_bbox,
            provider=payload.provider,
            collection_id=payload.collection_id,
            start_date="2020-01-01",
            end_date=fallback_end,
            max_cloud_cover=payload.max_cloud_cover,
            h3_resolution=payload.h3_resolution,
        )

    if not raster_result.get("features"):
        raise HotStreamOrchestratorError(
            "Raster processor returned no feature rows",
            code="RASTER_NO_FEATURES",
            status_code=422,
        )

    lakehouse_result = write_sentinel2_to_lakehouse(
        farm_id=farm_id,
        raster_result=raster_result,
    )

    return {
        "farm": farm,
        "repair": repair_result,
        "analysis_bbox": analysis_bbox,
        "raster_result": raster_result,
        "lakehouse_result": lakehouse_result,
    }
