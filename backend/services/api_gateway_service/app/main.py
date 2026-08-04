from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

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
