# from __future__ import annotations

# from fastapi import Depends, FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# from shared.config.settings import settings
# from shared.errors.api_errors import bad_request, unauthorized
# from shared.logging.json_logging import configure_json_logging
# from services.auth_service.app.schemas import (
#     AuthResponse,
#     HealthResponse,
#     LoginRequest,
#     LogoutRequest,
#     RefreshRequest,
#     SignupRequest,
#     SignupStartRequest,
#     SignupStartResponse,
#     SignupVerifyRequest,
#     SignupVerifyResponse,
#     SignupCompleteRequest,
#     UserPublic,
# )
# from services.auth_service.app.security import AuthSecurityError, decode_access_token
# from services.auth_service.app.service import (
#     AuthServiceError,
#     complete_signup,
#     get_current_user_from_id,
#     login,
#     logout,
#     refresh,
#     start_signup,
#     signup,
#     verify_signup_otp,
# )

# SERVICE_NAME = "auth_service"

# configure_json_logging(SERVICE_NAME)

# bearer_scheme = HTTPBearer(auto_error=False)

# app = FastAPI(
#     title="Auth Service",
#     version="1.0.0",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_allowed_origins_list,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/health/live", response_model=HealthResponse)
# def live():
#     return HealthResponse(
#         service=SERVICE_NAME,
#         status="live",
#         environment=settings.app_env,
#     )


# @app.get("/health/ready", response_model=HealthResponse)
# def ready():
#     return HealthResponse(
#         service=SERVICE_NAME,
#         status="ready",
#         environment=settings.app_env,
#     )


# @app.post("/v1/auth/signup", response_model=AuthResponse)
# def signup_endpoint(payload: SignupRequest):
#     try:
#         return AuthResponse(**signup(payload))
#     except AuthServiceError as exc:
#         raise bad_request(str(exc), code="AUTH_SIGNUP_ERROR") from exc


# @app.post("/v1/auth/signup/start", response_model=SignupStartResponse)
# def signup_start_endpoint(payload: SignupStartRequest):
#     try:
#         return SignupStartResponse(**start_signup(payload))
#     except AuthServiceError as exc:
#         raise bad_request(str(exc), code="AUTH_SIGNUP_ERROR_START") from exc


# @app.post("/v1/auth/signup/verify-otp", response_model=SignupVerifyResponse)
# def signup_verify_otp_endpoint(payload: SignupVerifyRequest):
#     try:
#         return SignupVerifyResponse(**verify_signup_otp(payload))
#     except AuthServiceError as exc:
#         raise bad_request(str(exc), code="AUTH_SIGNUP_ERROR_VERIFY") from exc


# @app.post("/v1/auth/signup/complete")
# def signup_complete_endpoint(payload: SignupCompleteRequest):
#     try:
#         return complete_signup(payload)
#     except AuthServiceError as exc:
#         raise bad_request(str(exc), code="AUTH_SIGNUP_ERROR_COMPLETE") from exc


# @app.post("/v1/auth/login", response_model=AuthResponse)
# def login_endpoint(payload: LoginRequest):
#     try:
#         return AuthResponse(**login(payload))
#     except AuthServiceError as exc:
#         raise unauthorized(str(exc), code="AUTH_LOGIN_ERROR") from exc


# @app.post("/v1/auth/refresh", response_model=AuthResponse)
# def refresh_endpoint(payload: RefreshRequest):
#     try:
#         return AuthResponse(**refresh(payload.refresh_token))
#     except AuthServiceError as exc:
#         raise unauthorized(str(exc), code="AUTH_REFRESH_ERROR") from exc


# @app.post("/v1/auth/logout")
# def logout_endpoint(payload: LogoutRequest):
#     try:
#         return logout(payload.refresh_token)
#     except AuthServiceError as exc:
#         raise bad_request(str(exc), code="AUTH_LOGOUT_ERROR") from exc


# def require_current_user(
#     credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
# ) -> UserPublic:
#     if credentials is None:
#         raise unauthorized("Missing bearer token", code="AUTH_REQUIRED")

#     try:
#         token_payload = decode_access_token(credentials.credentials)
#         user = get_current_user_from_id(token_payload["sub"])
#         return UserPublic(**user)
#     except (AuthSecurityError, AuthServiceError) as exc:
#         raise unauthorized(str(exc), code="AUTH_REQUIRED") from exc


# @app.get("/v1/auth/me", response_model=UserPublic)
# def me_endpoint(current_user: UserPublic = Depends(require_current_user)):
#     return current_user


from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config.settings import settings
from shared.logging.json_logging import configure_json_logging
from services.auth_service.app.dependencies import (
    AuthDependencyError,
    get_current_user_id,
)
from services.auth_service.app.schemas import (
    AuthResponse,
    GoogleAuthRequest,
    HealthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupCompleteRequest,
    SignupStartRequest,
    SignupStartResponse,
    SignupVerifyRequest,
    SignupVerifyResponse,
    UserPublic,
)
from services.auth_service.app.service import (
    AuthServiceError,
    complete_signup,
    get_current_user_from_id,
    login,
    login_with_google,
    logout,
    refresh,
    start_signup,
    verify_signup_otp,
)


SERVICE_NAME = "auth_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(title="MaatiTrace Auth Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(AuthDependencyError)
async def auth_dependency_error_handler(
    _request: Request,
    exc: AuthDependencyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": {
                "code": "AUTHORIZATION_ERROR",
                "message": str(exc),
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def _auth_error(
    exc: Exception,
    code: str,
    http_status: int = status.HTTP_400_BAD_REQUEST,
) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail={
            "code": code,
            "message": str(exc),
        },
    )


@app.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(
        service=SERVICE_NAME,
        status="live",
        environment=settings.app_env,
    )


@app.get("/health/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    return HealthResponse(
        service=SERVICE_NAME,
        status="ready",
        environment=settings.app_env,
    )


@app.post("/v1/auth/signup/start", response_model=SignupStartResponse, status_code=201)
def signup_start_endpoint(payload: SignupStartRequest):
    try:
        return start_signup(payload)
    except AuthServiceError as exc:
        raise _auth_error(exc, "SIGNUP_START_ERROR") from exc


@app.post("/v1/auth/signup/verify", response_model=SignupVerifyResponse)
def signup_verify_endpoint(payload: SignupVerifyRequest):
    try:
        return verify_signup_otp(payload)
    except AuthServiceError as exc:
        raise _auth_error(exc, "SIGNUP_VERIFY_ERROR") from exc


@app.post("/v1/auth/signup/verify-otp", response_model=SignupVerifyResponse)
def signup_verify_otp_compat_endpoint(payload: SignupVerifyRequest):
    try:
        return verify_signup_otp(payload)
    except AuthServiceError as exc:
        raise _auth_error(exc, "SIGNUP_VERIFY_ERROR") from exc


@app.post("/v1/auth/signup/complete", response_model=AuthResponse, status_code=201)
def signup_complete_endpoint(payload: SignupCompleteRequest):
    try:
        return complete_signup(payload)
    except AuthServiceError as exc:
        raise _auth_error(exc, "SIGNUP_COMPLETE_ERROR") from exc


@app.post("/v1/auth/login", response_model=AuthResponse)
def login_endpoint(payload: LoginRequest):
    try:
        return login(payload)
    except AuthServiceError as exc:
        raise _auth_error(exc, "LOGIN_ERROR", status.HTTP_401_UNAUTHORIZED) from exc


@app.post("/v1/auth/google", response_model=AuthResponse)
def google_endpoint(payload: GoogleAuthRequest):
    try:
        return login_with_google(payload.id_token)
    except AuthServiceError as exc:
        raise _auth_error(exc, "GOOGLE_AUTH_ERROR", status.HTTP_401_UNAUTHORIZED) from exc


@app.post("/v1/auth/refresh", response_model=AuthResponse)
def refresh_endpoint(payload: RefreshRequest):
    try:
        return refresh(payload.refresh_token)
    except AuthServiceError as exc:
        raise _auth_error(exc, "REFRESH_ERROR", status.HTTP_401_UNAUTHORIZED) from exc


@app.post("/v1/auth/logout")
def logout_endpoint(payload: LogoutRequest):
    try:
        return logout(payload.refresh_token)
    except AuthServiceError as exc:
        raise _auth_error(exc, "LOGOUT_ERROR") from exc


@app.get("/v1/auth/me", response_model=UserPublic)
def me_endpoint(user_id: str = Depends(get_current_user_id)):
    try:
        return get_current_user_from_id(user_id)
    except AuthDependencyError as exc:
        raise _auth_error(exc, "AUTHORIZATION_ERROR", status.HTTP_401_UNAUTHORIZED) from exc
    except AuthServiceError as exc:
        raise _auth_error(exc, "CURRENT_USER_ERROR", status.HTTP_401_UNAUTHORIZED) from exc