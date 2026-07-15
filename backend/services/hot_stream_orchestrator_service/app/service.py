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
    search_latest_sentinel2_scene,
    write_sentinel2_to_lakehouse,
    search_sentinel2_scene_candidates,
)
from services.hot_stream_orchestrator_service.app.schemas import FarmAnalysisMaterializeRequest
from services.hot_stream_orchestrator_service.app.repository import (
    create_pipeline_job,
    update_pipeline_job_stage,
    complete_pipeline_job,
    fail_pipeline_job,
    get_existing_scene_analysis_summary,
)


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


def _snapshot_date_from_scene(scene: dict[str, Any]) -> date:
    raw_datetime = scene.get("datetime")

    if not raw_datetime:
        return date.today()

    cleaned = str(raw_datetime).replace("Z", "+00:00")

    try:
        from datetime import datetime

        return datetime.fromisoformat(cleaned).date()
    except Exception:
        return date.today()


def _full_farm_bbox(farm: dict[str, Any]) -> list[float]:
    farm_bbox = _normalize_bbox(farm.get("bbox"))

    if farm_bbox is not None:
        return farm_bbox

    polygon = _normalize_polygon(farm.get("polygon_geojson"))
    if polygon:
        derived = _polygon_bbox_from_geojson(polygon)
        if derived:
            return derived

    raise HotStreamOrchestratorError(
        "Farm does not have valid bbox for STAC search.",
        code="FARM_BBOX_INVALID",
        status_code=422,
    )


def _static_h3_cells(farm: dict[str, Any]) -> list[int]:
    raw_cells = farm.get("h3_cells") or []

    if isinstance(raw_cells, str):
        try:
            raw_cells = json.loads(raw_cells)
        except Exception:
            raw_cells = []

    cells: list[int] = []

    for value in raw_cells:
        try:
            cells.append(int(value))
        except Exception:
            continue

    return sorted(set(cells))


def _build_cached_materialization_result(
    farm: dict[str, Any],
    scene: dict[str, Any],
    analysis_bbox: list[float],
    existing_summary: dict[str, Any],
) -> dict[str, Any]:
    row_count = int(existing_summary.get("row_count") or 0)
    total_pixel_count = int(existing_summary.get("total_pixel_count") or 0)
    total_valid_pixel_count = int(existing_summary.get("total_valid_pixel_count") or 0)
    total_cloud_pixel_count = int(existing_summary.get("total_cloud_pixel_count") or 0)

    raster_result = {
        "scene_id": scene["scene_id"],
        "scene_datetime": scene.get("datetime"),
        "scene_cloud_cover": scene.get("cloud_cover"),
        "row_count": row_count,
        "total_pixel_count": total_pixel_count,
        "total_valid_pixel_count": total_valid_pixel_count,
        "total_cloud_pixel_count": total_cloud_pixel_count,
        "h3_resolution": int(farm.get("h3_resolution") or 12),
        "source_assets_used": [],
        "features": [],
    }

    lakehouse_result = {
        "dataset": "h3_sentinel2_features",
        "row_count": row_count,
        "postgres_rows_written": 0,
        "parquet_rows_written": 0,
        "parquet_uri": existing_summary.get("parquet_uri") or "",
        "storage_mode": "cached_db",
        "snapshot_date": existing_summary.get("snapshot_date"),
    }

    return {
        "farm": farm,
        "repair": {"status": "ready"},
        "analysis_bbox": analysis_bbox,
        "raster_result": raster_result,
        "lakehouse_result": lakehouse_result,
        "pipeline_job": None,
        "from_cache": True,
    }

def _farm_valid_pixel_percentage(raster_result: dict[str, Any]) -> float:
    total_pixels = float(raster_result.get("total_pixel_count") or 0)
    valid_pixels = float(raster_result.get("total_valid_pixel_count") or 0)

    if total_pixels <= 0:
        return 0.0

    return round((valid_pixels / total_pixels) * 100.0, 6)


def _raster_has_any_valid_h3_cell(raster_result: dict[str, Any]) -> bool:
    features = raster_result.get("features") or []

    for item in features:
        if int(item.get("valid_pixel_count") or 0) > 0:
            return True

    return False

def materialize_farm_analysis(
    farm_id: UUID,
    payload: FarmAnalysisMaterializeRequest,
) -> dict[str, Any]:
    job = create_pipeline_job(
        farm_id=farm_id,
        job_type="farm_analysis_materialize",
        metadata={
            "payload": payload.model_dump() if hasattr(payload, "model_dump") else {},
        },
    )
    job_id = job["job_id"]

    try:
        update_pipeline_job_stage(job_id=job_id, stage="ensure_farm_ready", status="running")
        repair_result = ensure_farm_analysis_ready(farm_id)
        farm = repair_result["farm"]
        update_pipeline_job_stage(job_id=job_id, stage="ensure_farm_ready", status="succeeded")

        farm_bbox = _full_farm_bbox(farm)
        h3_cells = _static_h3_cells(farm)

        if not h3_cells:
            raise HotStreamOrchestratorError(
                "Farm has no static H3 cells. Re-register or repair the farm boundary.",
                code="FARM_H3_CELLS_MISSING",
                status_code=422,
            )

        expected_h3_count = len(h3_cells)

        update_pipeline_job_stage(job_id=job_id, stage="latest_scene_search", status="running")
        latest_scene = search_latest_sentinel2_scene(
            provider=payload.provider,
            collection_id=payload.collection_id,
            bbox=farm_bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
        )
        update_pipeline_job_stage(
            job_id=job_id,
            stage="latest_scene_search",
            status="succeeded",
            metadata={
                "latest_scene_id": latest_scene.get("scene_id"),
                "latest_scene_datetime": latest_scene.get("datetime"),
                "latest_scene_cloud_cover": latest_scene.get("cloud_cover"),
            },
        )

        scene_snapshot_date = _snapshot_date_from_scene(latest_scene)

        existing_summary = get_existing_scene_analysis_summary(
            farm_id=farm_id,
            scene_id=latest_scene["scene_id"],
            snapshot_date=scene_snapshot_date,
        )

        if (
            existing_summary
            and not payload.force_refresh
            and int(existing_summary.get("distinct_h3_count") or 0) >= expected_h3_count
        ):
            complete_pipeline_job(
                job_id=job_id,
                metadata={
                    "from_cache": True,
                    "scene_id": latest_scene["scene_id"],
                    "snapshot_date": scene_snapshot_date.isoformat(),
                    "expected_h3_count": expected_h3_count,
                    "existing_h3_count": int(existing_summary.get("distinct_h3_count") or 0),
                },
            )

            return _build_cached_materialization_result(
                farm=farm,
                scene=latest_scene,
                analysis_bbox=farm_bbox,
                existing_summary=existing_summary,
            )

        update_pipeline_job_stage(
            job_id=job_id,
            stage="raster_h3_processing",
            status="running",
            metadata={
                "scene_id": latest_scene["scene_id"],
                "snapshot_date": scene_snapshot_date.isoformat(),
                "expected_h3_count": expected_h3_count,
            },
        )

        raster_result = run_raster_preview_from_search(
            farm_id=farm_id,
            bbox=farm_bbox,
            provider=payload.provider,
            collection_id=payload.collection_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            h3_resolution=payload.h3_resolution,
            h3_cells_bigint=h3_cells,
        )

        feature_count = len(raster_result.get("features") or [])

        if feature_count < expected_h3_count:
            raise HotStreamOrchestratorError(
                f"Raster processor returned {feature_count} H3 rows, expected {expected_h3_count}.",
                code="RASTER_INCOMPLETE_H3_FEATURES",
                status_code=422,
            )

        update_pipeline_job_stage(
            job_id=job_id,
            stage="raster_h3_processing",
            status="succeeded",
            metadata={
                "scene_id": raster_result.get("scene_id"),
                "feature_count": feature_count,
                "expected_h3_count": expected_h3_count,
            },
        )

        update_pipeline_job_stage(job_id=job_id, stage="lakehouse_write", status="running")
        lakehouse_result = write_sentinel2_to_lakehouse(
            farm_id=farm_id,
            raster_result=raster_result,
        )
        update_pipeline_job_stage(
            job_id=job_id,
            stage="lakehouse_write",
            status="succeeded",
            metadata={
                "postgres_rows_written": lakehouse_result.get("postgres_rows_written"),
                "parquet_rows_written": lakehouse_result.get("parquet_rows_written"),
            },
        )

        complete_pipeline_job(
            job_id=job_id,
            metadata={
                "from_cache": False,
                "scene_id": raster_result.get("scene_id"),
                "features": feature_count,
                "expected_h3_count": expected_h3_count,
            },
        )

        return {
            "farm": farm,
            "repair": repair_result,
            "analysis_bbox": farm_bbox,
            "raster_result": raster_result,
            "lakehouse_result": lakehouse_result,
            "pipeline_job": job,
            "from_cache": False,
        }

    except HotStreamOrchestratorError as exc:
        try:
            fail_pipeline_job(
                job_id=job_id,
                error_code=exc.code if hasattr(exc, "code") else None,
                error_message=str(exc),
            )
        except Exception:
            pass
        raise

    except Exception as exc:
        try:
            fail_pipeline_job(
                job_id=job_id,
                error_code="UNEXPECTED_ERROR",
                error_message=str(exc),
            )
        except Exception:
            pass
        raise