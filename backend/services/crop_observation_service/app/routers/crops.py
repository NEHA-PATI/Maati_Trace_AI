from __future__ import annotations

from fastapi import APIRouter, Query

from services.crop_observation_service.app import service
from services.crop_observation_service.app.schemas import CropListResponse

router = APIRouter(prefix="/v1/crop-observations/crops", tags=["crops"])


@router.get("", response_model=CropListResponse)
def list_crops_endpoint(
    locale: str = Query(default="en-IN", max_length=10),
):
    return service.list_crops(locale=locale)
