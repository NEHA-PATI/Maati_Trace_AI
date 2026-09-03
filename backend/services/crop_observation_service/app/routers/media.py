from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

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


@router.put("/local-content/{object_key:path}", status_code=204)
async def upload_local_media_content_endpoint(
    object_key: str,
    request: Request,
    context: RequestContext = Depends(get_request_context),
):
    """Receives the raw bytes for a LOCAL-backend upload. `object_key` is
    only present in the URL so this mirrors an S3 PUT shape from the
    browser's point of view — the media_asset_id embedded in it is what we
    actually trust; nothing here lets the frontend choose a filesystem
    path (see storage/local.py resolve())."""
    from uuid import UUID as _UUID

    media_uuid = _UUID(object_key.rsplit("/", 1)[-1].split(".", 1)[0])
    data = await request.body()
    media_service.write_local_media_content(context, media_uuid, data)
    return Response(status_code=204)


@router.post("/{media_asset_id}/complete", response_model=MediaAssetResponse)
def complete_media_upload_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return media_service.complete_media_upload(context, media_asset_id)


@router.get("/{media_asset_id}/content")
def get_media_content_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    data, mime_type = media_service.get_media_content(context, media_asset_id)
    return Response(content=data, media_type=mime_type)
