from datetime import date
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.json_logging import configure_json_logging
from services.hot_stream_orchestrator_service.app.clients import (
    OrchestratorClientError,
)
from services.hot_stream_orchestrator_service.app.schemas import (
    FarmAnalysisMaterializeRequest,
    FarmAnalysisMaterializeResponse,
    HealthResponse,
)
from services.hot_stream_orchestrator_service.app.service import (
    HotStreamOrchestratorError,
    ensure_farm_analysis_ready,
    materialize_farm_analysis,
)
from services.analytics_query_service.app.repository import (
    get_farm_grid_cells,
    get_latest_features,
    get_latest_grid_values,
    materialize_grid_for_farm,
    materialize_trends_for_farm,
)

SERVICE_NAME = "hot_stream_orchestrator_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Hot Stream Orchestrator Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _raise_hot_stream_error(exc: HotStreamOrchestratorError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    ) from exc


@app.get("/health/live", response_model=HealthResponse)
def live():
    return HealthResponse(
        service=SERVICE_NAME,
        status="live",
        environment=settings.app_env,
    )


@app.get("/health/ready", response_model=HealthResponse)
def ready():
    return HealthResponse(
        service=SERVICE_NAME,
        status="ready",
        environment=settings.app_env,
    )


@app.post("/v1/hot-stream/farms/{farm_id}/repair")
def repair_farm_endpoint(farm_id: UUID):
    try:
        result = ensure_farm_analysis_ready(farm_id)
    except HotStreamOrchestratorError as exc:
        _raise_hot_stream_error(exc)
    except OrchestratorClientError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "FARM_REPAIR_ERROR", "message": str(exc)},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "FARM_REPAIR_ERROR", "message": f"Unexpected farm repair error: {exc}"},
        ) from exc

    return {
        "farm_id": str(farm_id),
        "status": "ready",
        "repaired_fields": result["repaired_fields"],
        "h3_cell_count": result["h3_cell_count"],
        "bbox": result["bbox"],
        "area_acres": result["area_acres"],
        "warnings": result["warnings"],
    }


@app.post(
    "/v1/farm-analysis/{farm_id}/materialize",
    response_model=FarmAnalysisMaterializeResponse,
)
def materialize_farm_analysis_endpoint(
    farm_id: UUID,
    payload: FarmAnalysisMaterializeRequest,
):
    try:
        result = materialize_farm_analysis(
            farm_id=farm_id,
            payload=payload,
        )
    except (HotStreamOrchestratorError, OrchestratorClientError) as exc:
        if isinstance(exc, HotStreamOrchestratorError):
            _raise_hot_stream_error(exc)
        raise HTTPException(
            status_code=400,
            detail={"code": "FARM_ANALYSIS_MATERIALIZE_ERROR", "message": str(exc)},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "FARM_ANALYSIS_MATERIALIZE_ERROR",
                "message": f"Unexpected farm analysis materialization error: {exc}",
            },
        ) from exc

    farm = result["farm"]
    raster_result = result["raster_result"]
    lakehouse_result = result["lakehouse_result"]

    return FarmAnalysisMaterializeResponse(
        farm_id=farm["farm_id"],
        farmer_id=farm["farmer_id"],
        fpo_id=farm.get("fpo_id"),
        district_name=farm["district_name"],
        block_name=farm.get("block_name"),
        block_code=farm.get("block_code"),
        scene_id=raster_result["scene_id"],
        scene_datetime=raster_result.get("scene_datetime"),
        scene_cloud_cover=raster_result.get("scene_cloud_cover"),
        raster_row_count=raster_result["row_count"],
        raster_total_pixel_count=raster_result["total_pixel_count"],
        raster_total_valid_pixel_count=raster_result["total_valid_pixel_count"],
        raster_total_cloud_pixel_count=raster_result["total_cloud_pixel_count"],
        lakehouse_dataset=lakehouse_result["dataset"],
        lakehouse_row_count=lakehouse_result["row_count"],
        postgres_rows_written=lakehouse_result["postgres_rows_written"],
        parquet_rows_written=lakehouse_result["parquet_rows_written"],
        parquet_uri=lakehouse_result["parquet_uri"],
        status="materialized",
        details={
            "analysis_bbox": result["analysis_bbox"],
            "storage_mode": lakehouse_result.get("storage_mode"),
            "snapshot_date": lakehouse_result.get("snapshot_date"),
        },
    )


@app.post(
    "/v1/hot-stream/farms/{farm_id}/materialize",
    response_model=FarmAnalysisMaterializeResponse,
)
def materialize_farm_alias_endpoint(
    farm_id: UUID,
    payload: FarmAnalysisMaterializeRequest,
):
    return materialize_farm_analysis_endpoint(farm_id, payload)


@app.post("/v1/hot-stream/farms/{farm_id}/trends/materialize")
def materialize_farm_trends_endpoint(farm_id: UUID):
    result = materialize_trends_for_farm(farm_id)
    return result


@app.post("/v1/hot-stream/farms/{farm_id}/grid/materialize")
def materialize_farm_grid_endpoint(farm_id: UUID):
    result = materialize_grid_for_farm(farm_id)
    return result


@app.post("/v1/hot-stream/farms/{farm_id}/full-refresh")
def full_refresh_farm_endpoint(farm_id: UUID, payload: FarmAnalysisMaterializeRequest | None = None):
    stages: list[dict[str, Any]] = []

    # 1. repair
    try:
        repair = ensure_farm_analysis_ready(farm_id)
        stages.append({"name": "repair", "status": "succeeded", "details": {"repaired_fields": repair.get("repaired_fields", []), "warnings": repair.get("warnings", [])}})
    except Exception as exc:
        stages.append({"name": "repair", "status": "failed", "code": getattr(exc, "code", "REPAIR_FAILED"), "message": str(exc)})
        return {"farm_id": str(farm_id), "status": "failed", "stages": stages}

    # 2. farm-analysis materialize
    try:
        mat_payload = payload or FarmAnalysisMaterializeRequest(start_date="2020-01-01", end_date=date.today().isoformat())
        analysis = materialize_farm_analysis(farm_id, mat_payload)
        stages.append({"name": "h3_analysis", "status": "succeeded", "details": {"raster_row_count": analysis.get("raster_result", {}).get("row_count"), "lakehouse_rows": analysis.get("lakehouse_result", {}).get("postgres_rows_written")}})
    except Exception as exc:
        stages.append({"name": "h3_analysis", "status": "failed", "code": getattr(exc, "code", "ANALYSIS_FAILED"), "message": str(exc)})
        return {"farm_id": str(farm_id), "status": "failed", "stages": stages}

    # 3. trends materialize
    try:
        trends = materialize_trends_for_farm(farm_id)
        stages.append({"name": "trends", "status": trends.get("status", "partial"), "details": {"trends_created": trends.get("trends_created")}})
    except Exception as exc:
        stages.append({"name": "trends", "status": "failed", "code": getattr(exc, "code", "TRENDS_FAILED"), "message": str(exc)})
        return {"farm_id": str(farm_id), "status": "partial", "stages": stages}

    # 4. grid materialize
    try:
        grid = materialize_grid_for_farm(farm_id)
        stages.append({"name": "grid", "status": grid.get("status", "partial"), "details": {"grid_cells_created": grid.get("grid_cells_created"), "grid_values_created": grid.get("grid_values_created")}})
    except Exception as exc:
        stages.append({"name": "grid", "status": "failed", "code": getattr(exc, "code", "GRID_FAILED"), "message": str(exc)})
        return {"farm_id": str(farm_id), "status": "partial", "stages": stages}

    return {"farm_id": str(farm_id), "status": "succeeded", "stages": stages}
