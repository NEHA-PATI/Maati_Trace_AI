from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, Query
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.config.settings import settings
from shared.db.postgres import engine
from shared.logging.json_logging import configure_json_logging
from services.farm_registry_service.app.dependencies import (
    RequestContext,
    get_request_context,
    require_internal_farm_service,
)
from services.farm_registry_service.app.errors import FarmRegistryError
from services.farm_registry_service.app.middleware import (
    CorrelationIdMiddleware,
    SecurityHeadersMiddleware,
    get_correlation_id,
)
from services.farm_registry_service.app.schemas import (
    FarmRegisterRequest,
    FarmResponse,
    FarmerFarmSummaryResponse,
    FpoFarmSummaryResponse,
    HealthResponse,
    InternalFarmResponse,
)
from services.farm_registry_service.app.service import (
    get_farm_for_requester,
    get_farmer_summary_for_requester,
    get_fpo_summary_for_requester,
    get_internal_farm,
    list_farmer_farms_for_requester,
    list_farms_for_requester,
    list_fpo_farms_for_requester,
    register_farm,
)

SERVICE_NAME = "farm_registry_service"

configure_json_logging(SERVICE_NAME)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("farm_registry_service_started", extra={"environment": settings.app_env})
    yield
    logger.info("farm_registry_service_stopped")


app = FastAPI(
    title="MaatiTrace Farm Registry Service",
    version="2.0.0-farm-only",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-FPO-ID",
        "X-Internal-Service-Token",
    ],
    expose_headers=["X-Correlation-ID"],
)


@app.exception_handler(FarmRegistryError)
async def farm_registry_error_handler(_request, exc: FarmRegistryError):
    log_method = logger.error if exc.status_code >= 500 else logger.warning
    log_method(
        "farm_registry_request_rejected",
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
                "message": "Check the submitted farm fields.",
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
        "farm_response_contract_failed",
        extra={
            "correlation_id": get_correlation_id(),
            "error_count": len(exc.errors()),
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "FARM_RESPONSE_CONTRACT_FAILED",
                "message": "The farm response could not be prepared.",
                "correlation_id": get_correlation_id(),
            }
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_request, exc: Exception):
    logger.exception("unhandled_farm_registry_error", extra={"correlation_id": get_correlation_id()})
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": "The farm request could not be completed.",
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


@app.get("/v1/fpos")
def list_fpos_compatibility_only():
    raise FarmRegistryError(
        "FPO_LIST_MOVED_TO_PROFILE_SERVICE",
        (
            "Compatibility route retained for existing AdminDashboard callers. "
            "Add GET /v1/profiles/fpos in profile_service, then move getFpos() to profileClient."
        ),
        501,
    )


@app.post("/v1/farms/register", response_model=FarmResponse, status_code=201)
def register_farm_endpoint(
    payload: FarmRegisterRequest,
    context: RequestContext = Depends(get_request_context),
):
    return register_farm(context, payload)


@app.get("/v1/farms", response_model=list[FarmResponse])
def list_farms_endpoint(
    fpo_id: UUID | None = None,
    farmer_id: UUID | None = None,
    district_name: str | None = Query(default=None, max_length=100),
    block_name: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    context: RequestContext = Depends(get_request_context),
):
    return list_farms_for_requester(
        context,
        fpo_id=fpo_id,
        farmer_id=farmer_id,
        district_name=district_name,
        block_name=block_name,
        limit=limit,
        offset=offset,
    )


@app.get("/v1/farms/{farm_id}", response_model=FarmResponse)
def get_farm_endpoint(
    farm_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return get_farm_for_requester(context, farm_id)


@app.get("/v1/farmers/{farmer_id}/farms", response_model=list[FarmResponse])
def list_farmer_farms_endpoint(
    farmer_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return list_farmer_farms_for_requester(context, farmer_id)


@app.get("/v1/farmers/{farmer_id}/summary", response_model=FarmerFarmSummaryResponse)
def get_farmer_summary_endpoint(
    farmer_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return get_farmer_summary_for_requester(context, farmer_id)


@app.get("/v1/fpos/{fpo_id}/farms", response_model=list[FarmResponse])
def list_fpo_farms_endpoint(
    fpo_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return list_fpo_farms_for_requester(context, fpo_id)


@app.get("/v1/fpos/{fpo_id}/summary", response_model=FpoFarmSummaryResponse)
def get_fpo_summary_endpoint(
    fpo_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return get_fpo_summary_for_requester(context, fpo_id)


@app.get(
    "/internal/v1/farms/{farm_id}",
    response_model=InternalFarmResponse,
    dependencies=[Depends(require_internal_farm_service)],
)
def get_internal_farm_endpoint(farm_id: UUID):
    return get_internal_farm(farm_id)
