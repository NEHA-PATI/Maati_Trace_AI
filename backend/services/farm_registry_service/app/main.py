import json
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.errors.api_errors import bad_request, not_found
from shared.logging.json_logging import configure_json_logging
from shared.schemas.health import HealthResponse
from services.farm_registry_service.app.auth_client import (
    FarmRegistryAuthClientError,
    get_current_user_from_auth_service,
)
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
    get_farmer_by_user_id,
    get_farmer_summary,
    get_fpo,
    get_fpo_by_user,
    get_fpo_summary,
    list_farmers_by_fpo,
    list_farms_by_fpo,
    list_farms_by_farmer,
    list_farms,
    list_fpos,
    update_farmer_profile_by_user_id,
    update_fpo_profile_by_user_id,
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


@app.get("/v1/fpos", response_model=list[FPOResponse])
def list_fpos_endpoint():
    return [FPOResponse(**row) for row in list_fpos()]


@app.get("/v1/fpos/me", response_model=FPOResponse)
def get_my_fpo_endpoint(authorization: str | None = Header(default=None)):
    try:
        current_user = get_current_user_from_auth_service(authorization)
    except FarmRegistryAuthClientError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": str(exc)},
        ) from exc

    result = get_fpo_by_user(current_user["user_id"])
    if result is None:
        raise not_found("Current user is not linked to an FPO")
    return FPOResponse(**result)


@app.patch("/v1/farmers/me/profile", response_model=FarmerResponse)
def patch_my_farmer_profile(payload: dict, authorization: str | None = Header(default=None)):
    current_user = get_current_user_from_auth_service(authorization)
    result = update_farmer_profile_by_user_id(current_user["user_id"], payload)
    if result is None:
        raise not_found("Farmer not found")
    return FarmerResponse(**result)


@app.get("/v1/farmers/me/profile-export")
def export_my_farmer_profile(authorization: str | None = Header(default=None)):
    current_user = get_current_user_from_auth_service(authorization)
    result = get_farmer_by_user_id(current_user["user_id"])
    if result is None:
      raise not_found("Farmer not found")
    return result


@app.patch("/v1/fpos/me/profile", response_model=FPOResponse)
def patch_my_fpo_profile(payload: dict, authorization: str | None = Header(default=None)):
    current_user = get_current_user_from_auth_service(authorization)
    result = update_fpo_profile_by_user_id(current_user["user_id"], payload)
    if result is None:
        raise not_found("FPO not found")
    return FPOResponse(**result)


@app.get("/v1/fpos/me/profile-export")
def export_my_fpo_profile(authorization: str | None = Header(default=None)):
    current_user = get_current_user_from_auth_service(authorization)
    result = get_fpo_by_user(current_user["user_id"])
    if result is None:
        raise not_found("FPO not found")
    return result


@app.get("/v1/fpos/{fpo_id}", response_model=FPOResponse)
def get_fpo_endpoint(fpo_id: UUID):
    result = get_fpo(fpo_id)

    if result is None:
        raise not_found("FPO not found")

    return FPOResponse(**result)


@app.get("/v1/fpos/{fpo_id}/summary")
def get_fpo_summary_endpoint(fpo_id: UUID):
    return get_fpo_summary(fpo_id)


@app.get("/v1/fpos/{fpo_id}/farmers", response_model=list[FarmerResponse])
def get_fpo_farmers_endpoint(fpo_id: UUID):
    return [FarmerResponse(**row) for row in list_farmers_by_fpo(fpo_id)]


@app.get("/v1/fpos/{fpo_id}/farms", response_model=list[FarmResponse])
def get_fpo_farms_endpoint(fpo_id: UUID):
    return [FarmResponse(**row) for row in list_farms_by_fpo(fpo_id)]


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


@app.get("/v1/farmers/me", response_model=FarmerResponse)
def get_my_farmer_endpoint(authorization: str | None = Header(default=None)):
    try:
        current_user = get_current_user_from_auth_service(authorization)
    except FarmRegistryAuthClientError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": str(exc)},
        ) from exc

    if current_user.get("role") != "farmer":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "NOT_A_FARMER_USER",
                "message": "Current user is not a farmer user",
            },
        )

    result = get_farmer_by_user_id(current_user["user_id"])
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "FARMER_PROFILE_NOT_FOUND",
                "message": "No farmer profile is linked to this user",
            },
        )
    return FarmerResponse(**result)


@app.get("/v1/farmers/{farmer_id}", response_model=FarmerResponse)
def get_farmer_endpoint(farmer_id: UUID):
    result = get_farmer(farmer_id)

    if result is None:
        raise not_found("Farmer not found")

    return FarmerResponse(**result)


@app.get("/v1/farmers/{farmer_id}/summary")
def get_farmer_summary_endpoint(farmer_id: UUID):
    return get_farmer_summary(farmer_id)


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


@app.get("/v1/farms", response_model=list[FarmResponse])
def list_farms_endpoint(
    fpo_id: UUID | None = None,
    farmer_id: UUID | None = None,
    district_name: str | None = None,
    block_name: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
):
    return [
        FarmResponse(**row)
        for row in list_farms(
            fpo_id=fpo_id,
            farmer_id=farmer_id,
            district_name=district_name,
            block_name=block_name,
            limit=limit,
            offset=offset,
        )
    ]


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
