from fastapi import FastAPI, Query

from shared.config.settings import settings
from shared.logging.json_logging import configure_json_logging
from shared.schemas.health import HealthResponse
from services.district_boundary_service.app.location_repository import (
    get_service_stats,
    list_blocks_by_district,
    list_districts,
    list_states,
    validate_location,
)
from services.district_boundary_service.app.schemas import (
    BlockResponse,
    DistrictResponse,
    LocationValidateRequest,
    LocationValidateResponse,
    ServiceStatsResponse,
    StateResponse,
)

SERVICE_NAME = "district_boundary_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="District Boundary Service",
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


@app.get("/v1/location/stats", response_model=ServiceStatsResponse)
def stats():
    return get_service_stats()


@app.get("/v1/states", response_model=list[StateResponse])
def get_states():
    return list_states()


@app.get("/v1/districts", response_model=list[DistrictResponse])
def get_districts(
    state_name: str = Query(default="Odisha", min_length=2, max_length=100),
):
    return list_districts(state_name=state_name)


@app.get("/v1/blocks", response_model=list[BlockResponse])
def get_blocks(
    district_name: str = Query(..., min_length=2, max_length=100),
    state_name: str = Query(default="Odisha", min_length=2, max_length=100),
):
    return list_blocks_by_district(
        district_name=district_name,
        state_name=state_name,
    )


@app.post("/v1/location/validate", response_model=LocationValidateResponse)
def validate_location_endpoint(payload: LocationValidateRequest):
    return validate_location(
        state_name=payload.state_name,
        district_name=payload.district_name,
        block_name=payload.block_name,
        block_code=payload.block_code,
    )