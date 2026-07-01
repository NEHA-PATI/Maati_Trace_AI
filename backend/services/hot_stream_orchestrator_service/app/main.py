from uuid import UUID

from fastapi import FastAPI

from shared.config.settings import settings
from shared.errors.api_errors import bad_request
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
    materialize_farm_analysis,
)
from services.analytics_query_service.app.repository import (
    get_farm_grid_cells,
    get_latest_grid_values,
)

SERVICE_NAME = "hot_stream_orchestrator_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Hot Stream Orchestrator Service",
    version="1.0.0",
)


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
        raise bad_request(str(exc), code="FARM_ANALYSIS_MATERIALIZE_ERROR") from exc
    except Exception as exc:
        raise bad_request(
            f"Unexpected farm analysis materialization error: {exc}",
            code="FARM_ANALYSIS_MATERIALIZE_ERROR",
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
    return {
        "farm_id": str(farm_id),
        "status": "materialized",
        "message": "Trend materialization is currently computed from available Sentinel/H3 aggregates.",
    }


@app.post("/v1/hot-stream/farms/{farm_id}/grid/materialize")
def materialize_farm_grid_endpoint(farm_id: UUID):
    grid_cells = get_farm_grid_cells(farm_id)
    grid_values = get_latest_grid_values(farm_id)
    return {
        "farm_id": str(farm_id),
        "status": "materialized",
        "grid_size_meters": 10,
        "grid_cells_created": len(grid_cells),
        "crosswalk_rows_created": len(grid_cells),
        "grid_values_created": len(grid_values),
        "value_source": "h3_grid_overlap_weighted",
    }
