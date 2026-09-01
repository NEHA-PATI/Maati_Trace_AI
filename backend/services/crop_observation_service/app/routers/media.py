from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from services.crop_observation_service.app import media_service
from services.crop_observation_service.app.dependencies import (
    RequestContext,
    get_request_context,
)
from services.crop_observation_service.app.schemas import (
    MediaAssetResponse,
    MediaUploadRequest,
    MediaUploadResponse,
)

router = APIRouter(prefix="/v1/crop-observations/media", tags=["media"])


@router.post("/uploads", response_model=MediaUploadResponse, status_code=201)
def request_media_upload_endpoint(
    payload: MediaUploadRequest,
    context: RequestContext = Depends(get_request_context),
):
    return media_service.request_media_upload(context, payload)


@router.post("/{media_asset_id}/complete", response_model=MediaAssetResponse)
def complete_media_upload_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return media_service.complete_media_upload(context, media_asset_id)
