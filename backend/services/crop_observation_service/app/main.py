from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.config.settings import settings
from shared.db.postgres import engine
from shared.logging.json_logging import configure_json_logging
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.middleware import (
    CorrelationIdMiddleware,
    SecurityHeadersMiddleware,
    get_correlation_id,
)
from services.crop_observation_service.app.routers import (
    admin,
    crops,
    farm_crops,
    history,
    media,
    observations,
)
from services.crop_observation_service.app.schemas import HealthResponse

SERVICE_NAME = "crop_observation_service"

configure_json_logging(SERVICE_NAME)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("crop_observation_service_started", extra={"environment": settings.app_env})
    yield
    logger.info("crop_observation_service_stopped")


app = FastAPI(
    title="MaatiTrace Crop Observation Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
)


@app.exception_handler(CropObservationError)
async def crop_observation_error_handler(_request, exc: CropObservationError):
    log_method = logger.error if exc.status_code >= 500 else logger.warning
    log_method(
        "crop_observation_request_rejected",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "correlation_id": get_correlation_id(),
            "internal_message": exc.internal_message,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail(get_correlation_id())},
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "VALIDATION_ERROR",
                "message": "Check the submitted fields.",
                "correlation_id": get_correlation_id(),
                "fields": [
                    {
                        "type": item.get("type"),
                        "loc": item.get("loc"),
                        "msg": item.get("msg"),
                    }
                    for item in exc.errors()
                ],
            }
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_error_handler(_request, exc: ResponseValidationError):
    logger.exception(
        "crop_observation_response_contract_failed",
        extra={
            "correlation_id": get_correlation_id(),
            "error_count": len(exc.errors()),
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "CROP_OBSERVATION_RESPONSE_CONTRACT_FAILED",
                "message": "The crop observation response could not be prepared.",
                "correlation_id": get_correlation_id(),
            }
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_request, exc: Exception):
    logger.exception("unhandled_crop_observation_error", extra={"correlation_id": get_correlation_id()})
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": "The crop observation request could not be completed.",
                "correlation_id": get_correlation_id(),
            }
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.get("/health/live", response_model=HealthResponse)
def live():
    return HealthResponse(service=SERVICE_NAME, status="live", environment=settings.app_env)


@app.get("/health/ready", response_model=HealthResponse)
def ready():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return HealthResponse(service=SERVICE_NAME, status="ready", environment=settings.app_env)


app.include_router(crops.router)
app.include_router(farm_crops.router)
app.include_router(observations.router)
app.include_router(media.router)
app.include_router(history.router)
app.include_router(admin.router)
