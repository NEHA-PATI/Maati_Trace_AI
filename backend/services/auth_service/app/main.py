from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from shared.db.postgres import engine
from shared.logging.json_logging import configure_json_logging
from services.auth_service.app.config_validation import AuthConfig, get_auth_config, validate_auth_config
from services.auth_service.app.dependencies import (
    RequestContext,
    get_current_principal,
    get_request_context,
    require_roles,
    validate_cookie_request,
)
from services.auth_service.app.errors import AuthError
from services.auth_service.app.logging_context import get_correlation_id, get_logger, log_event
from services.auth_service.app.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from services.auth_service.app.rate_limit import get_rate_limiter
from services.auth_service.app.schemas import (
    AuthResponse,
    FpoAccessRequestAdminView,
    FpoAccessRequestCreate,
    FpoAccessRequestListResponse,
    FpoAccessRequestPublicResponse,
    FpoAccessReviewRequest,
    GoogleAuthRequest,
    InvitationAcceptRequest,
    InvitationCreateRequest,
    InvitationCreateResponse,
    InvitationValidationResponse,
    HealthResponse,
    LoginRequest,
    MessageResponse,
    PasswordForgotRequest,
    PasswordResetRequest,
    SignupCancelRequest,
    SignupCompleteRequest,
    SignupResendRequest,
    SignupResendResponse,
    SignupStartRequest,
    SignupStartResponse,
    SignupVerifyRequest,
    SignupVerifyResponse,
    UserPublic,
)
from services.auth_service.app.service import (
    IssuedSession,
    accept_invitation,
    cancel_signup,
    create_invitation_for_admin,
    complete_signup,
    forgot_password,
    get_current_user,
    get_fpo_access_requests_for_admin,
    login,
    login_with_google,
    logout,
    logout_all,
    reset_password,
    review_fpo_access_request_for_admin,
    refresh_session,
    resend_signup_otp,
    start_signup,
    submit_fpo_access_request,
    validate_invitation,
    verify_signup_otp,
)


SERVICE_NAME = "auth_service"
configure_json_logging(SERVICE_NAME)
logger = get_logger(__name__)
bootstrap_config = AuthConfig.from_env()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config = get_auth_config()
    validate_auth_config(config)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    if config.rate_limit_enabled:
        get_rate_limiter().client.ping()
    log_event(logger, logging.INFO, "auth_service_started", environment=config.app_env)
    yield
    log_event(logger, logging.INFO, "auth_service_stopped")


app = FastAPI(
    title="MaatiTrace Auth Service",
    version="2.0.0-phase2",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(bootstrap_config.trusted_hosts),
)
if bootstrap_config.app_env == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(bootstrap_config.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
        "X-Device-ID",
        "X-Correlation-ID",
    ],
    expose_headers=["X-Correlation-ID", "Retry-After"],
)


@app.exception_handler(AuthError)
async def auth_error_handler(_request: Request, exc: AuthError) -> JSONResponse:
    headers: dict[str, str] = {"X-Correlation-ID": get_correlation_id()}
    if exc.retry_after is not None:
        headers["Retry-After"] = str(exc.retry_after)
    log_event(
        logger,
        logging.WARNING if exc.status_code < 500 else logging.ERROR,
        "auth_request_rejected",
        code=exc.code,
        status_code=exc.status_code,
        internal_message=exc.internal_message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail()},
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    safe_errors = []
    for item in exc.errors():
        safe_errors.append(
            {
                "type": item.get("type"),
                "loc": item.get("loc"),
                "msg": item.get("msg"),
            }
        )
    log_event(logger, logging.INFO, "request_validation_failed", errors=safe_errors)
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "VALIDATION_ERROR",
                "message": "Check the submitted fields and try again.",
                "correlation_id": get_correlation_id(),
                "fields": safe_errors,
            }
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled authentication service error")
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "INTERNAL_ERROR",
                "message": "The request could not be completed.",
                "correlation_id": get_correlation_id(),
            }
        },
        headers={"X-Correlation-ID": get_correlation_id()},
    )


def _auth_response(issued: IssuedSession) -> AuthResponse:
    config = get_auth_config()
    return AuthResponse(
        access_token=issued.access_token,
        expires_in_seconds=config.access_token_expire_minutes * 60,
        user=issued.user,
    )


def _set_session_cookies(response: Response, issued: IssuedSession) -> None:
    config = get_auth_config()
    max_age = config.refresh_token_expire_days * 86400
    response.set_cookie(
        key=config.refresh_cookie_name,
        value=issued.refresh_token,
        max_age=max_age,
        httponly=True,
        secure=config.cookie_secure,
        samesite=config.cookie_same_site,
        path=config.refresh_cookie_path,
        domain=config.cookie_domain,
    )
    response.set_cookie(
        key=config.csrf_cookie_name,
        value=issued.csrf_token,
        max_age=max_age,
        httponly=False,
        secure=config.cookie_secure,
        samesite=config.cookie_same_site,
        path="/",
        domain=config.cookie_domain,
    )


def _clear_session_cookies(response: Response) -> None:
    config = get_auth_config()
    response.delete_cookie(
        config.refresh_cookie_name,
        path=config.refresh_cookie_path,
        domain=config.cookie_domain,
    )
    response.delete_cookie(
        config.csrf_cookie_name,
        path="/",
        domain=config.cookie_domain,
    )


def _enforce(scope: str, *dimensions: tuple[str, str | None]) -> None:
    get_rate_limiter().enforce(scope, dimensions)


@app.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, status="live", environment=get_auth_config().app_env)


@app.get("/health/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    config = get_auth_config()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    if config.rate_limit_enabled:
        get_rate_limiter().client.ping()
    return HealthResponse(service=SERVICE_NAME, status="ready", environment=config.app_env)


@app.post("/v1/auth/signup/start", response_model=SignupStartResponse, status_code=status.HTTP_201_CREATED)
def signup_start_endpoint(
    payload: SignupStartRequest,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "signup_start",
        ("ip", context.ip_address),
        ("email", str(payload.email)),
        ("phone", payload.phone_number),
        ("device", context.device_id_hash),
    )
    return start_signup(payload, context)


@app.post("/v1/auth/signup/resend", response_model=SignupResendResponse)
def signup_resend_endpoint(
    payload: SignupResendRequest,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "signup_resend",
        ("ip", context.ip_address),
        ("session", str(payload.signup_session_id)),
        ("device", context.device_id_hash),
    )
    return resend_signup_otp(payload.signup_session_id, context)


@app.post("/v1/auth/signup/verify", response_model=SignupVerifyResponse)
def signup_verify_endpoint(
    payload: SignupVerifyRequest,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "signup_verify",
        ("ip", context.ip_address),
        ("session", str(payload.signup_session_id)),
        ("device", context.device_id_hash),
    )
    return verify_signup_otp(payload.signup_session_id, payload.otp, context)


@app.post("/v1/auth/signup/cancel")
def signup_cancel_endpoint(
    payload: SignupCancelRequest,
    context: RequestContext = Depends(get_request_context),
):
    return cancel_signup(payload.signup_session_id, payload.reason, context)


@app.post("/v1/auth/signup/complete", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup_complete_endpoint(
    payload: SignupCompleteRequest,
    response: Response,
    context: RequestContext = Depends(get_request_context),
):
    issued = complete_signup(payload.signup_session_id, context)
    _set_session_cookies(response, issued)
    return _auth_response(issued)


@app.post("/v1/auth/login", response_model=AuthResponse)
def login_endpoint(
    payload: LoginRequest,
    response: Response,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "login",
        ("ip", context.ip_address),
        ("identifier", payload.identifier.strip().lower()),
        ("device", context.device_id_hash),
    )
    issued = login(payload, context)
    _set_session_cookies(response, issued)
    return _auth_response(issued)


@app.post("/v1/auth/google", response_model=AuthResponse)
def google_endpoint(
    payload: GoogleAuthRequest,
    response: Response,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "google_login",
        ("ip", context.ip_address),
        ("device", context.device_id_hash),
    )
    issued = login_with_google(payload.id_token, context)
    _set_session_cookies(response, issued)
    return _auth_response(issued)


@app.post("/v1/auth/refresh", response_model=AuthResponse)
def refresh_endpoint(
    response: Response,
    refresh_token: str = Depends(validate_cookie_request),
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "refresh",
        ("ip", context.ip_address),
        ("device", context.device_id_hash),
    )
    issued = refresh_session(refresh_token, context)
    _set_session_cookies(response, issued)
    return _auth_response(issued)


@app.post("/v1/auth/logout")
def logout_endpoint(
    response: Response,
    refresh_token: str = Depends(validate_cookie_request),
    context: RequestContext = Depends(get_request_context),
):
    result = logout(refresh_token, context)
    _clear_session_cookies(response)
    return result


@app.post("/v1/auth/logout-all")
def logout_all_endpoint(
    response: Response,
    principal: dict[str, str] = Depends(get_current_principal),
    _refresh_token: str = Depends(validate_cookie_request),
    context: RequestContext = Depends(get_request_context),
):
    result = logout_all(principal["user_id"], principal["session_id"], context)
    _clear_session_cookies(response)
    return result


@app.post("/v1/auth/password/forgot", response_model=MessageResponse)
def password_forgot_endpoint(
    payload: PasswordForgotRequest,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "password_forgot",
        ("ip", context.ip_address),
        ("email", str(payload.email)),
        ("device", context.device_id_hash),
    )
    return forgot_password(payload, context)


@app.post("/v1/auth/password/reset", response_model=MessageResponse)
def password_reset_endpoint(
    payload: PasswordResetRequest,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "password_reset",
        ("ip", context.ip_address),
        ("token", payload.token[:16]),
        ("device", context.device_id_hash),
    )
    return reset_password(payload, context)


@app.post(
    "/v1/auth/fpo-access-requests",
    response_model=FpoAccessRequestPublicResponse,
    status_code=status.HTTP_201_CREATED,
)
def fpo_access_request_endpoint(
    payload: FpoAccessRequestCreate,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "fpo_access",
        ("ip", context.ip_address),
        ("email", str(payload.contact_email)),
        ("phone", payload.contact_phone),
        ("device", context.device_id_hash),
    )
    return submit_fpo_access_request(payload, context)


@app.get(
    "/v1/auth/admin/fpo-access-requests",
    response_model=FpoAccessRequestListResponse,
)
def admin_fpo_access_requests_endpoint(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _principal: dict[str, str] = Depends(require_roles("admin")),
):
    if status_filter not in {None, "pending", "approved", "rejected", "closed"}:
        raise AuthError("INVALID_STATUS_FILTER", "The status filter is invalid.", 422)
    return get_fpo_access_requests_for_admin(
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@app.patch(
    "/v1/auth/admin/fpo-access-requests/{request_id}",
    response_model=FpoAccessRequestAdminView,
)
def admin_review_fpo_access_request_endpoint(
    request_id: str,
    payload: FpoAccessReviewRequest,
    principal: dict[str, str] = Depends(require_roles("admin")),
    context: RequestContext = Depends(get_request_context),
):
    return review_fpo_access_request_for_admin(
        request_id=request_id,
        payload=payload,
        admin_user_id=principal["user_id"],
        context=context,
    )


@app.post(
    "/v1/auth/admin/invitations",
    response_model=InvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_invitation_endpoint(
    payload: InvitationCreateRequest,
    principal: dict[str, str] = Depends(require_roles("admin")),
    context: RequestContext = Depends(get_request_context),
):
    return create_invitation_for_admin(
        payload,
        admin_user_id=principal["user_id"],
        context=context,
    )


@app.get("/v1/auth/invitations/validate", response_model=InvitationValidationResponse)
def validate_invitation_endpoint(
    token: str = Query(min_length=40, max_length=512),
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "invitation_validate",
        ("ip", context.ip_address),
        ("token", token[:16]),
        ("device", context.device_id_hash),
    )
    return validate_invitation(token)


@app.post("/v1/auth/invitations/accept", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def accept_invitation_endpoint(
    payload: InvitationAcceptRequest,
    response: Response,
    context: RequestContext = Depends(get_request_context),
):
    _enforce(
        "invitation_accept",
        ("ip", context.ip_address),
        ("token", payload.token[:16]),
        ("phone", payload.phone_number),
        ("device", context.device_id_hash),
    )
    issued = accept_invitation(payload, context)
    _set_session_cookies(response, issued)
    return _auth_response(issued)


@app.get("/v1/auth/me", response_model=UserPublic)
def me_endpoint(principal: dict[str, str] = Depends(get_current_principal)):
    return get_current_user(principal["user_id"])