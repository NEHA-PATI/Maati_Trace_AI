from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.errors.api_errors import bad_request
from shared.logging.json_logging import configure_json_logging
from services.lakehouse_writer_service.app.schemas import (
    HealthResponse,
    Sentinel2LakehouseWriteRequest,
    Sentinel2LakehouseWriteResponse,
)
from services.lakehouse_writer_service.app.service import (
    LakehouseWriterError,
    write_sentinel2_features,
)

SERVICE_NAME = "lakehouse_writer_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Lakehouse Writer Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    "/v1/lakehouse/sentinel2/write",
    response_model=Sentinel2LakehouseWriteResponse,
)
def write_sentinel2(payload: Sentinel2LakehouseWriteRequest):
    try:
        result = write_sentinel2_features(payload)
    except LakehouseWriterError as exc:
        raise bad_request(str(exc), code="LAKEHOUSE_WRITE_ERROR") from exc
    except Exception as exc:
        raise bad_request(
            f"Unexpected lakehouse writer error: {exc}",
            code="LAKEHOUSE_WRITE_ERROR",
        ) from exc

    return Sentinel2LakehouseWriteResponse(
        dataset=result["dataset"],
        farm_id=result["farm_id"],
        farmer_id=result["farmer_id"],
        fpo_id=result["fpo_id"],
        snapshot_date=result["snapshot_date"],
        scene_id=result["scene_id"],
        row_count=result["row_count"],
        postgres_rows_written=result["postgres_rows_written"],
        parquet_rows_written=result["parquet_rows_written"],
        storage_mode=settings.storage_mode,
        parquet_uri=result["parquet_uri"],
    )
