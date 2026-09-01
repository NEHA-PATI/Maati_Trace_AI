from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from services.crop_observation_service.app import service
from services.crop_observation_service.app.dependencies import (
    RequestContext,
    get_request_context,
)
from services.crop_observation_service.app.schemas import (
    CropCycleCreateRequest,
    CropCycleResponse,
    FarmCropCreateRequest,
    FarmCropResponse,
)

router = APIRouter(prefix="/v1/crop-observations", tags=["farm-crops"])


@router.get("/farms/{farm_id}/crops", response_model=list[FarmCropResponse])
def list_farm_crops_endpoint(
    farm_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return service.list_farm_crops_for_farm(context, farm_id)


@router.post(
    "/farms/{farm_id}/crops",
    response_model=FarmCropResponse,
    status_code=201,
)
def attach_crop_to_farm_endpoint(
    farm_id: UUID,
    payload: FarmCropCreateRequest,
    context: RequestContext = Depends(get_request_context),
):
    return service.attach_crop_to_farm(context, farm_id, payload)


@router.post(
    "/farm-crops/{farm_crop_id}/cycles",
    response_model=CropCycleResponse,
    status_code=201,
)
def start_crop_cycle_endpoint(
    farm_crop_id: UUID,
    payload: CropCycleCreateRequest,
    context: RequestContext = Depends(get_request_context),
):
    return service.start_crop_cycle(context, farm_crop_id, payload)
