from contextlib import asynccontextmanager

import httpx

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api_gateway_service.app.proxy import (
    UPSTREAM_CLIENT_STATE_KEY,
    GatewayProxyError,
    create_upstream_client,
    get_route_targets,
    proxy_health_request,
    proxy_request,
)
from services.api_gateway_service.app.schemas import HealthResponse
from shared.config.settings import settings
from shared.logging.json_logging import configure_json_logging
from services.auth_service.app.dependencies import require_roles
from services.auth_service.app.errors import AuthError

SERVICE_NAME = "api_gateway_service"

configure_json_logging(SERVICE_NAME)


@asynccontextmanager
async def lifespan(application: FastAPI):
    client = create_upstream_client()
    setattr(application.state, UPSTREAM_CLIENT_STATE_KEY, client)
    try:
        yield
    finally:
        await client.aclose()


app = FastAPI(
    title="MaatiTrace API Gateway Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AuthError)
async def auth_error_handler(_request: Request, exc: AuthError) -> JSONResponse:
    """Return authentication failures as 401/403 instead of an unhandled 500."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail()},
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


@app.get("/api/routes")
def routes():
    return {
        "gateway": SERVICE_NAME,
        "routes": get_route_targets(),
    }


@app.post("/fpo-uploads", include_in_schema=False)
async def upload_fpo_file(file: UploadFile = File(...)):
    """Upload an FPO file to the configured Microsoft Graph folder."""
    config = (
        settings.microsoft_tenant_id,
        settings.microsoft_client_id,
        settings.microsoft_client_secret,
        settings.microsoft_drive_id,
        settings.microsoft_folder_id,
    )
    if not all(config):
        raise HTTPException(status_code=503, detail="Microsoft Graph upload is not configured")

    content = await file.read()
    token_url = f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/oauth2/v2.0/token"
    async with httpx.AsyncClient(timeout=60) as client:
        token_response = await client.post(token_url, data={
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        })
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        upload_url = (
            f"https://graph.microsoft.com/v1.0/drives/{settings.microsoft_drive_id}"
            f"/items/{settings.microsoft_folder_id}:/{file.filename}:/content"
        )
        upload_response = await client.put(
            upload_url,
            content=content,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": file.content_type or "application/octet-stream",
            },
        )
        if upload_response.is_error:
            raise HTTPException(status_code=502, detail="Microsoft Graph rejected the upload")

    return {"filename": file.filename, "status": "uploaded"}


@app.get("/api/health/{service_name}/{check}", response_model=HealthResponse)
async def service_health(service_name: str, check: str, request: Request):
    try:
        return await proxy_health_request(
            service_name=service_name,
            check=check,
            request=request,
        )
    except GatewayProxyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "API_GATEWAY_PROXY_ERROR", "message": str(exc)},
        ) from exc


@app.api_route(
    "/api/historical-acquisition/{rest_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def historical_acquisition_proxy(
    rest_path: str,
    request: Request,
    principal: dict[str, str] = Depends(require_roles("admin")),
):
    """Authorize in Backend 1, then call ML with a gateway-owned identity."""
    try:
        return await proxy_request(
            prefix="historical-acquisition",
            rest_path=rest_path,
            request=request,
            service_context=principal,
        )
    except GatewayProxyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "ML_GATEWAY_PROXY_ERROR", "message": str(exc)},
        ) from exc


@app.api_route(
    "/api/lakehouse-inventory/{rest_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def lakehouse_inventory_proxy(
    rest_path: str,
    request: Request,
    principal: dict[str, str] = Depends(require_roles("admin")),
):
    """Authorize inventory operations in Backend 1 before calling DB 2 service."""
    try:
        return await proxy_request(
            prefix="lakehouse-inventory",
            rest_path=rest_path,
            request=request,
            service_context=principal,
        )
    except GatewayProxyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "ML_INVENTORY_GATEWAY_ERROR", "message": str(exc)},
        ) from exc


@app.api_route(
    "/api/scientific-standardization/{rest_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def scientific_standardization_proxy(
    rest_path: str,
    request: Request,
    principal: dict[str, str] = Depends(require_roles("admin")),
):
    """Authorize scientific processing operations in Backend 1."""
    try:
        return await proxy_request(
            prefix="scientific-standardization",
            rest_path=rest_path,
            request=request,
            service_context=principal,
        )
    except GatewayProxyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "ML_SCIENCE_GATEWAY_ERROR", "message": str(exc)},
        ) from exc


@app.api_route(
    "/api/admin/fpo/{rest_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    dependencies=[Depends(require_roles("admin"))],
)
async def admin_fpo_proxy(rest_path: str, request: Request):
    try:
        return await proxy_request(
            prefix="admin-fpo",
            rest_path=rest_path,
            request=request,
        )
    except GatewayProxyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "API_GATEWAY_PROXY_ERROR", "message": str(exc)},
        ) from exc


@app.api_route(
    "/api/{prefix}/{rest_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def gateway_proxy(prefix: str, rest_path: str, request: Request):
    try:
        return await proxy_request(
            prefix=prefix,
            rest_path=rest_path,
            request=request,
        )
    except GatewayProxyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "API_GATEWAY_PROXY_ERROR", "message": str(exc)},
        ) from exc
