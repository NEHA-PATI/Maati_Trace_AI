from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, Response

from services.crop_observation_service.app import media_service, observation_service, repository as repo
from services.crop_observation_service.app.dependencies import (
    RequestContext,
    get_request_context,
)
from services.crop_observation_service.app.schemas import (
    MediaAccessResponse,
    MediaAssetResponse,
    MediaUploadRequest,
    MediaUploadResponse,
    OwnerMediaOut,
)

router = APIRouter(prefix="/v1/crop-observations/media", tags=["media"])


@router.get("", response_model=list[OwnerMediaOut])
def list_owner_media_endpoint(
    owner_type: str = Query(..., pattern="^(DAILY_STAGE|PRACTICE)$"),
    owner_id: UUID = Query(...),
    context: RequestContext = Depends(get_request_context),
):
    owner = media_service._resolve_owner_context(owner_type, owner_id)
    observation_service.resolve_cycle_and_authorize(context, owner["cycle"]["crop_cycle_id"])
    rows = repo.list_media_for_owner(owner_type, owner_id)
    return [
        OwnerMediaOut(
            **row,
            content_url=f"/v1/crop-observations/media/{row['media_asset_id']}/content",
        )
        for row in rows
        if row.get("upload_status") == "READY"
    ]


@router.post("/uploads", response_model=MediaUploadResponse, status_code=201)
def request_media_upload_endpoint(
    payload: MediaUploadRequest,
    context: RequestContext = Depends(get_request_context),
):
    return media_service.request_media_upload(context, payload)


@router.put("/local-content/{media_asset_id}", status_code=204)
async def upload_local_media_content_endpoint(
    media_asset_id: UUID,
    request: Request,
    context: RequestContext = Depends(get_request_context),
):
    data = await request.body()
    media_service.write_local_media_content(context, media_asset_id, data)
    return Response(status_code=204)


@router.post("/{media_asset_id}/complete", response_model=MediaAssetResponse)
def complete_media_upload_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return media_service.complete_media_upload(context, media_asset_id)


@router.delete("/{media_asset_id}", status_code=204)
def delete_media_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    media_service.delete_media(context, media_asset_id)
    return Response(status_code=204)


@router.get("/{media_asset_id}/access", response_model=MediaAccessResponse)
def get_media_access_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    return media_service.get_media_access(context, media_asset_id)


@router.get("/{media_asset_id}/content")
def get_media_content_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    data, mime_type, redirect_url = media_service.get_media_content(context, media_asset_id)
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=307)
    return Response(content=data or b"", media_type=mime_type)
