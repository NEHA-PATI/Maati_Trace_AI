from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.logging.json_logging import configure_json_logging
from shared.schemas.health import HealthResponse
from shared.security.local_auth import (
    CurrentUserUnavailableError,
    InvalidAccessTokenError,
    MissingAuthorizationError,
    PrincipalLookupError,
    load_current_user,
)
from services.observability_service.app.repository import (
    ObservabilityRepositoryError,
    farm_feature_status,
    feature_processing_summary,
    formula_status,
    processing_runs,
    source_status,
)

SERVICE_NAME = "observability_service"
configure_json_logging(SERVICE_NAME)

app = FastAPI(title=SERVICE_NAME.replace("_", " ").title(), version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(authorization: str | None) -> dict:
    try:
        user = load_current_user(authorization)
    except MissingAuthorizationError as exc:
        raise HTTPException(status_code=401, detail="Authentication is required") from exc
    except (InvalidAccessTokenError, CurrentUserUnavailableError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except PrincipalLookupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required")
    return user


def repo_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ObservabilityRepositoryError as exc:
        raise HTTPException(status_code=500, detail={"code": "OBSERVABILITY_QUERY_ERROR", "message": str(exc)}) from exc


@app.get("/health/live", response_model=HealthResponse)
def live():
    return HealthResponse(service=SERVICE_NAME, status="live", environment=settings.app_env)


@app.get("/health/ready", response_model=HealthResponse)
def ready():
    return HealthResponse(service=SERVICE_NAME, status="ready", environment=settings.app_env)


@app.get("/v1/observability/feature-processing/summary")
def feature_summary(authorization: str | None = Header(default=None, alias="Authorization")):
    require_admin(authorization)
    return repo_call(feature_processing_summary)


@app.get("/v1/observability/feature-processing/runs")
def feature_runs(
    limit: int = Query(default=100, ge=1, le=500),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    require_admin(authorization)
    return {"items": repo_call(processing_runs, limit)}


@app.get("/v1/observability/feature-processing/sources")
def feature_sources(authorization: str | None = Header(default=None, alias="Authorization")):
    require_admin(authorization)
    return {"items": repo_call(source_status)}


@app.get("/v1/observability/feature-processing/formulas")
def feature_formulas(authorization: str | None = Header(default=None, alias="Authorization")):
    require_admin(authorization)
    return repo_call(formula_status)


@app.get("/v1/observability/feature-processing/farms/{farm_id}")
def feature_farm(farm_id: UUID, authorization: str | None = Header(default=None, alias="Authorization")):
    require_admin(authorization)
    result = repo_call(farm_feature_status, farm_id)
    if not result:
        raise HTTPException(status_code=404, detail="Farm not found")
    return result
