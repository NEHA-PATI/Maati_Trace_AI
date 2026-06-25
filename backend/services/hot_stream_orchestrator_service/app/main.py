from fastapi import FastAPI

from shared.config.settings import settings
from shared.logging.json_logging import configure_json_logging
from shared.schemas.health import HealthResponse

SERVICE_NAME = "hot_stream_orchestrator_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title=SERVICE_NAME.replace("_", " ").title(),
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
