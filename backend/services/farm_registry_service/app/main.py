import json
from uuid import UUID

from fastapi import FastAPI

from shared.config.settings import settings
from shared.errors.api_errors import bad_request, not_found
from shared.logging.json_logging import configure_json_logging
from shared.schemas.health import HealthResponse
from services.farm_registry_service.app.area_calculator import (
    FarmGeometryError,
    calculate_area_acres,
)
from services.farm_registry_service.app.external_clients import (
    ExternalServiceError,
    create_h3_preview,
    validate_location,
)
from services.farm_registry_service.app.repository import (
    FarmRegistryRepositoryError,
    create_farm,
    create_farmer,
    create_fpo,
    get_farm,
    get_farmer,
    get_fpo,
    list_farms_by_farmer,
)
from services.farm_registry_service.app.schemas import (
    FPOCreateRequest,
    FPOResponse,
    FarmRegisterRequest,
    FarmResponse,
    FarmerCreateRequest,
    FarmerResponse,
)

SERVICE_NAME = "farm_registry_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Farm Registry Service",
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


@app.post("/v1/fpos", response_model=FPOResponse)
def create_fpo_endpoint(payload: FPOCreateRequest):
    try:
        location = validate_location(
            state_name=payload.state_name,
            district_name=payload.district_name,
            block_name=payload.block_name,
            block_code=payload.block_code,
        )

        data = payload.model_dump()
        data["state_name"] = location["state_name"]
        data["district_name"] = location["district_name"]
        data["block_name"] = location["block_name"]
        data["block_code"] = location["block_code"]

        result = create_fpo(data)
        return FPOResponse(**result)

    except ExternalServiceError as exc:
        raise bad_request(str(exc), code="LOCATION_VALIDATION_ERROR") from exc
    except FarmRegistryRepositoryError as exc:
        raise bad_request(str(exc), code="FPO_CREATE_ERROR") from exc


@app.get("/v1/fpos/{fpo_id}", response_model=FPOResponse)
def get_fpo_endpoint(fpo_id: UUID):
    result = get_fpo(fpo_id)

    if result is None:
        raise not_found("FPO not found")

    return FPOResponse(**result)


@app.post("/v1/farmers", response_model=FarmerResponse)
def create_farmer_endpoint(payload: FarmerCreateRequest):
    try:
        location = validate_location(
            state_name=payload.state_name,
            district_name=payload.district_name,
            block_name=payload.block_name,
            block_code=payload.block_code,
        )

        data = payload.model_dump()
        data["district_code"] = location["district_code"]
        data["district_name"] = location["district_name"]
        data["state_name"] = location["state_name"]
        data["block_name"] = location["block_name"]
        data["block_code"] = location["block_code"]

        result = create_farmer(data)
        return FarmerResponse(**result)

    except ExternalServiceError as exc:
        raise bad_request(str(exc), code="LOCATION_VALIDATION_ERROR") from exc
    except FarmRegistryRepositoryError as exc:
        raise bad_request(str(exc), code="FARMER_CREATE_ERROR") from exc


@app.get("/v1/farmers/{farmer_id}", response_model=FarmerResponse)
def get_farmer_endpoint(farmer_id: UUID):
    result = get_farmer(farmer_id)

    if result is None:
        raise not_found("Farmer not found")

    return FarmerResponse(**result)


@app.post("/v1/farms/register", response_model=FarmResponse)
def register_farm_endpoint(payload: FarmRegisterRequest):
    farmer = get_farmer(payload.farmer_id)

    if farmer is None:
        raise not_found("Farmer not found")

    try:
        location = validate_location(
            state_name=payload.state_name,
            district_name=payload.district_name,
            block_name=payload.block_name,
            block_code=payload.block_code,
        )

        h3_result = create_h3_preview(
            polygon=payload.polygon,
            resolution=payload.h3_resolution,
            max_cells=None,
        )

        area_acres = calculate_area_acres(payload.polygon)

        data = {
            "farmer_id": str(payload.farmer_id),
            "fpo_id": str(payload.fpo_id) if payload.fpo_id else None,
            "farm_name": payload.farm_name,
            "survey_number": payload.survey_number,
            "state_name": location["state_name"],
            "district_name": location["district_name"],
            "district_code": location["district_code"],
            "block_name": location["block_name"],
            "block_code": location["block_code"],
            "village_name": payload.village_name,
            "polygon_geojson": json.dumps(payload.polygon),
            "h3_resolution": h3_result["resolution"],
            "h3_cells": h3_result["h3_cells_bigint"],
            "h3_cell_count": h3_result["cell_count"],
            "area_acres": area_acres,
            "bbox": json.dumps(h3_result["bbox"]),
        }

        result = create_farm(data)
        return FarmResponse(**result)

    except ExternalServiceError as exc:
        raise bad_request(str(exc), code="EXTERNAL_VALIDATION_ERROR") from exc
    except FarmGeometryError as exc:
        raise bad_request(str(exc), code="FARM_GEOMETRY_ERROR") from exc
    except FarmRegistryRepositoryError as exc:
        raise bad_request(str(exc), code="FARM_CREATE_ERROR") from exc
    
    
@app.get("/v1/farms/{farm_id}", response_model=FarmResponse)
def get_farm_endpoint(farm_id: UUID):
    result = get_farm(farm_id)

    if result is None:
        raise not_found("Farm not found")

    return FarmResponse(**result)


@app.get("/v1/farmers/{farmer_id}/farms", response_model=list[FarmResponse])
def list_farmer_farms_endpoint(farmer_id: UUID):
    farmer = get_farmer(farmer_id)

    if farmer is None:
        raise not_found("Farmer not found")

    return [FarmResponse(**row) for row in list_farms_by_farmer(farmer_id)]
