import asyncio
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, HTTPException
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
    LatestAnalysisRequest,
    Sentinel2HistoryBackfillRequest,
)
from services.hot_stream_orchestrator_service.app.service import (
    HotStreamOrchestratorError,
    ensure_farm_analysis_ready,
    materialize_farm_analysis,
    run_latest_analysis,
)
from services.hot_stream_orchestrator_service.app.environment_schemas import (
    EnvironmentRefreshRequest,
    EnvironmentRefreshResponse,
)
from services.hot_stream_orchestrator_service.app.environment_service import (
    EnvironmentRefreshError,
    materialize_environment,
)
from services.hot_stream_orchestrator_service.app.history_backfill import (
    backfill_sentinel2_history,
)
from services.hot_stream_orchestrator_service.app.repository import (
    get_or_create_active_latest_analysis_job,
    get_latest_pipeline_job,
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


async def _run_latest_analysis_in_background(
    farm_id: UUID,
    payload: LatestAnalysisRequest,
    job_id: str,
) -> None:
    """Run blocking source adapters off the HTTP event loop."""

    await asyncio.to_thread(
        run_latest_analysis,
        farm_id,
        payload,
        job_id=job_id,
    )

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


@app.post("/v1/hot-stream/farms/{farm_id}/run-latest-analysis", status_code=202)
def run_latest_analysis_endpoint(
    farm_id: UUID,
    payload: LatestAnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """Queue the one complete normal farm-to-intelligence workflow."""

    # Validate before creating a queued job so a bad farm returns immediately
    # and cannot leave an orphaned analysis record.
    try:
        ensure_farm_analysis_ready(farm_id)
    except HotStreamOrchestratorError as exc:
        _raise_hot_stream_error(exc)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "LATEST_ANALYSIS_VALIDATION_ERROR", "message": str(exc)},
        ) from exc

    job, already_running = get_or_create_active_latest_analysis_job(
        farm_id=farm_id,
        metadata={"request": payload.model_dump(), "analysis_status": "queued"},
    )
    job_id = str(job["job_id"])
    if already_running:
        return {
            "farm_id": str(farm_id),
            "job_id": job_id,
            "status": "already_running",
            "current_stage": job.get("current_stage"),
        }
    background_tasks.add_task(
        _run_latest_analysis_in_background,
        farm_id,
        payload,
        job_id,
    )
    return {
        "farm_id": str(farm_id),
        "job_id": job_id,
        "status": "queued",
        "current_stage": "queued",
    }


@app.get("/v1/hot-stream/farms/{farm_id}/analysis-status")
def latest_analysis_status_endpoint(farm_id: UUID):
    job = get_latest_pipeline_job(farm_id)
    if not job:
        return {
            "farm_id": str(farm_id),
            "status": "not_started",
            "current_stage": None,
            "stages": [],
        }
    metadata = job.get("metadata") or {}
    job_status = job.get("status")
    analysis_status = metadata.get("analysis_status") or job_status
    if job_status == "failed":
        analysis_status = "failed"
    elif job_status in {"pending", "running"} and analysis_status == "queued":
        analysis_status = "running"
    return {
        "farm_id": str(farm_id),
        "job_id": str(job["job_id"]),
        "status": analysis_status,
        "job_status": job_status,
        "current_stage": job.get("current_stage"),
        "stages": metadata.get("stages") or [],
        "error_code": job.get("error_code"),
        "error_message": job.get("error_message"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "updated_at": job.get("updated_at"),
    }


@app.post("/v1/hot-stream/farms/{farm_id}/full-refresh")
def full_refresh_farm_endpoint(
    farm_id: UUID,
    payload: FarmAnalysisMaterializeRequest | None = None,
):
    """Compatibility alias for the canonical synchronous workflow."""

    if payload is None:
        canonical = LatestAnalysisRequest()
    else:
        canonical = LatestAnalysisRequest(
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            h3_resolution=payload.h3_resolution,
            max_candidate_scenes=payload.max_candidate_scenes,
            provider=payload.provider,
            collection_id=payload.collection_id,
            force_refresh=payload.force_refresh,
        )
    return run_latest_analysis(farm_id, canonical)


@app.post(
    "/v1/hot-stream/farms/{farm_id}/environment-refresh",
    response_model=EnvironmentRefreshResponse,
)
def environment_refresh_endpoint(farm_id: UUID, payload: EnvironmentRefreshRequest):
    """
    Explicit environment-only diagnostic/admin operation.

    Normal farmer traffic uses run-latest-analysis, which invokes one
    all-dataset environmental stage (including Sentinel-2) before calculated
    intelligence. This endpoint remains useful for an operator retry of that
    same stage.
    """
    try:
        result = materialize_environment(farm_id, payload)
        return EnvironmentRefreshResponse(**result)
    except EnvironmentRefreshError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "ENVIRONMENT_REFRESH_ERROR", "message": str(exc)},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "ENVIRONMENT_REFRESH_ERROR", "message": str(exc)},
        ) from exc


@app.post("/v1/hot-stream/farms/{farm_id}/sentinel2/history-backfill")
def sentinel2_history_backfill_endpoint(farm_id: UUID, payload: Sentinel2HistoryBackfillRequest):
    try:
        return backfill_sentinel2_history(farm_id, payload)
    except HotStreamOrchestratorError as exc:
        _raise_hot_stream_error(exc)
    except OrchestratorClientError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "S2_HISTORY_BACKFILL_ERROR", "message": str(exc)},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "S2_HISTORY_BACKFILL_ERROR", "message": str(exc)},
        ) from exc
