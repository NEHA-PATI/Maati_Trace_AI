from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.exceptions import (
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
)

from shared.db.postgres import engine
from shared.logging.json_logging import (
    configure_json_logging,
)

from services.profile_service.app.config_validation import (
    ProfileConfig,
    get_profile_config,
    validate_profile_config,
)
from services.profile_service.app.dependencies import (
    RequestContext,
    get_request_context,
    require_internal_service,
)
from services.profile_service.app.errors import (
    ProfileError,
)
from services.profile_service.app.middleware import (
    CorrelationIdMiddleware,
    SecurityHeadersMiddleware,
    get_correlation_id,
)
from services.profile_service.app.schemas import (
    FarmerProfileEnvelope,
    FarmerProfileResponse,
    FarmerProfileUpdate,
    FarmerValidationResponse,
    FpoProfileEnvelope,
    FpoProfileSetupRequest,
    FpoProfileUpdate,
    FpoValidationResponse,
    HealthResponse,
    ProfileEnvelope,
    ProfileExportResponse,
)
from services.profile_service.app.service import (
    export_my_profile,
    get_farmer_for_requester,
    get_fpo_farmers_for_requester,
    get_fpo_for_requester,
    get_my_profile,
    setup_my_fpo_profile,
    update_my_farmer_profile,
    update_my_fpo_profile,
    validate_farmer_internal,
    validate_fpo_internal,
)


SERVICE_NAME = "profile_service"

configure_json_logging(SERVICE_NAME)
logger = logging.getLogger(__name__)

bootstrap_config = ProfileConfig.from_env()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config = get_profile_config()
    validate_profile_config(config)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    logger.info(
        "profile_service_started",
        extra={
            "environment": config.app_env,
        },
    )

    yield

    logger.info("profile_service_stopped")


app = FastAPI(
    title="MaatiTrace Profile Service",
    version="1.0.0-phase1",
    lifespan=lifespan,
)

app.add_middleware(
    CorrelationIdMiddleware
)
app.add_middleware(
    SecurityHeadersMiddleware
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(
        bootstrap_config.trusted_hosts
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        bootstrap_config.cors_allowed_origins
    ),
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-FPO-ID",
        "X-Internal-Service-Token",
    ],
    expose_headers=[
        "X-Correlation-ID",
    ],
)


@app.exception_handler(ProfileError)
async def profile_error_handler(
    _request,
    exc: ProfileError,
):
    log_method = (
        logger.error
        if exc.status_code >= 500
        else logger.warning
    )

    log_method(
        "profile_request_rejected",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "correlation_id": (
                get_correlation_id()
            ),
            "internal_message": (
                exc.internal_message
            ),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail(
                get_correlation_id()
            )
        },
        headers={
            "X-Correlation-ID": (
                get_correlation_id()
            )
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request,
    exc: RequestValidationError,
):
    safe_errors = [
        {
            "type": item.get("type"),
            "loc": item.get("loc"),
            "msg": item.get("msg"),
        }
        for item in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "VALIDATION_ERROR",
                "message": (
                    "Check the submitted profile fields."
                ),
                "correlation_id": (
                    get_correlation_id()
                ),
                "fields": safe_errors,
            }
        },
        headers={
            "X-Correlation-ID": (
                get_correlation_id()
            )
        },
    )


@app.exception_handler(
    ResponseValidationError
)
async def response_validation_error_handler(
    _request,
    exc: ResponseValidationError,
):
    error_locations = [
        list(item.get("loc", ()))
        for item in exc.errors()[:20]
    ]

    logger.exception(
        "profile_response_contract_failed",
        extra={
            "correlation_id": (
                get_correlation_id()
            ),
            "error_count": len(
                exc.errors()
            ),
            "error_locations": (
                error_locations
            ),
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": (
                    "PROFILE_RESPONSE_CONTRACT_FAILED"
                ),
                "message": (
                    "The profile response could not "
                    "be prepared."
                ),
                "correlation_id": (
                    get_correlation_id()
                ),
            }
        },
        headers={
            "X-Correlation-ID": (
                get_correlation_id()
            )
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(
    _request,
    exc: Exception,
):
    logger.exception(
        "Unhandled profile service error"
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": (
                    "The profile request could not be completed."
                ),
                "correlation_id": (
                    get_correlation_id()
                ),
            }
        },
        headers={
            "X-Correlation-ID": (
                get_correlation_id()
            )
        },
    )


@app.get(
    "/health/live",
    response_model=HealthResponse,
)
def live():
    return HealthResponse(
        service=SERVICE_NAME,
        status="live",
        environment=bootstrap_config.app_env,
    )


@app.get(
    "/health/ready",
    response_model=HealthResponse,
)
def ready():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return HealthResponse(
        service=SERVICE_NAME,
        status="ready",
        environment=get_profile_config().app_env,
    )


@app.get(
    "/v1/profiles/me",
    response_model=ProfileEnvelope,
)
def read_my_profile(
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return get_my_profile(context)


@app.patch(
    "/v1/profiles/farmer/me",
    response_model=FarmerProfileEnvelope,
)
async def patch_my_farmer_profile(
    payload: FarmerProfileUpdate,
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return await update_my_farmer_profile(
        context,
        payload,
    )


@app.post(
    "/v1/profiles/fpo/setup",
    response_model=FpoProfileEnvelope,
    status_code=201,
)
async def create_my_fpo_profile(
    payload: FpoProfileSetupRequest,
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return await setup_my_fpo_profile(
        context,
        payload,
    )


@app.patch(
    "/v1/profiles/fpo/me",
    response_model=FpoProfileEnvelope,
)
async def patch_my_fpo_profile(
    payload: FpoProfileUpdate,
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return await update_my_fpo_profile(
        context,
        payload,
    )


@app.get(
    "/v1/profiles/me/export",
    response_model=ProfileExportResponse,
)
def export_current_profile(
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return export_my_profile(context)


@app.get(
    "/v1/profiles/farmers/{farmer_id}",
    response_model=FarmerProfileEnvelope,
)
def read_farmer_profile(
    farmer_id: UUID,
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return get_farmer_for_requester(
        context,
        farmer_id,
    )


@app.get(
    "/v1/profiles/fpos/{fpo_id}",
    response_model=FpoProfileEnvelope,
)
def read_fpo_profile(
    fpo_id: UUID,
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return get_fpo_for_requester(
        context,
        fpo_id,
    )


@app.get(
    "/v1/profiles/fpos/{fpo_id}/farmers",
    response_model=list[
        FarmerProfileResponse
    ],
)
def read_fpo_farmers(
    fpo_id: UUID,
    context: RequestContext = Depends(
        get_request_context
    ),
):
    return get_fpo_farmers_for_requester(
        context,
        fpo_id,
    )


@app.get(
    (
        "/internal/v1/farmers/"
        "{farmer_id}/validation"
    ),
    response_model=FarmerValidationResponse,
    dependencies=[
        Depends(require_internal_service)
    ],
)
def validate_farmer_for_internal_service(
    farmer_id: UUID,
):
    return validate_farmer_internal(
        farmer_id
    )


@app.get(
    "/internal/v1/fpos/{fpo_id}/validation",
    response_model=FpoValidationResponse,
    dependencies=[
        Depends(require_internal_service)
    ],
)
def validate_fpo_for_internal_service(
    fpo_id: UUID,
):
    return validate_fpo_internal(
        fpo_id
    )
