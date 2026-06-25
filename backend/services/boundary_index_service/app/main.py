from fastapi import FastAPI

from shared.config.settings import settings
from shared.errors.api_errors import bad_request
from shared.logging.json_logging import configure_json_logging
from shared.schemas.health import HealthResponse
from services.boundary_index_service.app.h3_indexer import (
    BoundaryIndexError,
    polygon_to_h3_bigints,
)
from services.boundary_index_service.app.schemas import (
    H3PreviewRequest,
    H3PreviewResponse,
)

SERVICE_NAME = "boundary_index_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Boundary Index Service",
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


@app.post("/v1/h3/preview", response_model=H3PreviewResponse)
def preview_h3_cells(payload: H3PreviewRequest):
    try:
        result = polygon_to_h3_bigints(
            geojson=payload.polygon,
            resolution=payload.resolution,
            include_cells=payload.include_cells,
            max_cells=payload.max_cells,
        )
        return H3PreviewResponse(**result)
    except BoundaryIndexError as exc:
        raise bad_request(str(exc), code="BOUNDARY_INDEX_ERROR") from exc
