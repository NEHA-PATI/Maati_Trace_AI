from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.errors.api_errors import bad_request
from shared.logging.json_logging import configure_json_logging
from services.api_gateway_service.app.proxy import (
    GatewayProxyError,
    get_route_targets,
    proxy_request,
)
from services.api_gateway_service.app.schemas import HealthResponse

SERVICE_NAME = "api_gateway_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="MaatiTrace API Gateway Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
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
        raise bad_request(str(exc), code="API_GATEWAY_PROXY_ERROR") from exc