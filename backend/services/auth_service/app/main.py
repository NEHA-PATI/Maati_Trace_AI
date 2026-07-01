from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.config.settings import settings
from shared.errors.api_errors import bad_request, unauthorized
from shared.logging.json_logging import configure_json_logging
from services.auth_service.app.schemas import (
    AuthResponse,
    HealthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    UserPublic,
)
from services.auth_service.app.security import AuthSecurityError, decode_access_token
from services.auth_service.app.service import (
    AuthServiceError,
    get_current_user_from_id,
    login,
    logout,
    refresh,
    signup,
)

SERVICE_NAME = "auth_service"

configure_json_logging(SERVICE_NAME)

bearer_scheme = HTTPBearer(auto_error=False)

app = FastAPI(
    title="Auth Service",
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


@app.post("/v1/auth/signup", response_model=AuthResponse)
def signup_endpoint(payload: SignupRequest):
    try:
        return AuthResponse(**signup(payload))
    except AuthServiceError as exc:
        raise bad_request(str(exc), code="AUTH_SIGNUP_ERROR") from exc


@app.post("/v1/auth/login", response_model=AuthResponse)
def login_endpoint(payload: LoginRequest):
    try:
        return AuthResponse(**login(payload))
    except AuthServiceError as exc:
        raise unauthorized(str(exc), code="AUTH_LOGIN_ERROR") from exc


@app.post("/v1/auth/refresh", response_model=AuthResponse)
def refresh_endpoint(payload: RefreshRequest):
    try:
        return AuthResponse(**refresh(payload.refresh_token))
    except AuthServiceError as exc:
        raise unauthorized(str(exc), code="AUTH_REFRESH_ERROR") from exc


@app.post("/v1/auth/logout")
def logout_endpoint(payload: LogoutRequest):
    try:
        return logout(payload.refresh_token)
    except AuthServiceError as exc:
        raise bad_request(str(exc), code="AUTH_LOGOUT_ERROR") from exc


def require_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic:
    if credentials is None:
        raise unauthorized("Missing bearer token", code="AUTH_REQUIRED")

    try:
        token_payload = decode_access_token(credentials.credentials)
        user = get_current_user_from_id(token_payload["sub"])
        return UserPublic(**user)
    except (AuthSecurityError, AuthServiceError) as exc:
        raise unauthorized(str(exc), code="AUTH_REQUIRED") from exc


@app.get("/v1/auth/me", response_model=UserPublic)
def me_endpoint(current_user: UserPublic = Depends(require_current_user)):
    return current_user