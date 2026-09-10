from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, Response

from shared.config.settings import settings

from services.crop_observation_service.app import (
    admin_extended_service as svc,
    admin_service,
    repository as repo,
)
from services.crop_observation_service.app.admin_extended_schemas import (
    AdminOverviewOut,
    AdminPracticeRecordOut,
    AdminRecordDetailOut,
    AdminSystemStatusOut,
    RecordReviewOut,
    RecordReviewUpdateRequest,
    SystemMediaBindingOut,
    SystemMediaCompleteResponse,
    SystemMediaUploadRequest,
    SystemMediaUploadResponse,
    TtsBatchOut,
    TtsBatchRequest,
)
from services.crop_observation_service.app.dependencies import RequestContext, get_request_context
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.storage import local as local_storage
from services.crop_observation_service.app.storage import s3 as s3_storage

router = APIRouter(prefix="/v1/crop-observations/admin", tags=["admin-v2"])


@router.get("/overview", response_model=AdminOverviewOut)
def overview_endpoint(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    context: RequestContext = Depends(get_request_context),
):
    return svc.get_overview(context, from_date=from_date, to_date=to_date)


@router.get("/records", response_model=list[AdminPracticeRecordOut])
def list_records_endpoint(
    crop_code: str | None = Query(default=None),
    stage_code: str | None = Query(default=None),
    practice_code: str | None = Query(default=None),
    crop_status: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    farmer_user_id: UUID | None = Query(default=None),
    farm_id: UUID | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    has_issue_image: bool | None = Query(default=None),
    has_practice_image: bool | None = Query(default=None),
    has_voice: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: RequestContext = Depends(get_request_context),
):
    return svc.list_records(
        context,
        crop_code=crop_code,
        stage_code=stage_code,
        practice_code=practice_code,
        crop_status=crop_status,
        review_status=review_status,
        severity=severity,
        farmer_user_id=farmer_user_id,
        farm_id=farm_id,
        from_date=from_date,
        to_date=to_date,
        has_issue_image=has_issue_image,
        has_practice_image=has_practice_image,
        has_voice=has_voice,
        limit=limit,
        offset=offset,
    )


@router.get("/records/{record_id}", response_model=AdminRecordDetailOut)
def get_record_endpoint(record_id: UUID, context: RequestContext = Depends(get_request_context)):
    return svc.get_record(context, record_id)


@router.put("/records/{record_id}/review", response_model=RecordReviewOut)
def update_record_review_endpoint(
    record_id: UUID,
    payload: RecordReviewUpdateRequest,
    context: RequestContext = Depends(get_request_context),
):
    return svc.update_review(context, record_id, payload)


@router.get("/issues", response_model=list[AdminPracticeRecordOut])
def list_issues_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: RequestContext = Depends(get_request_context),
):
    return svc.list_issues(context, limit=limit, offset=offset)


@router.get("/media/{media_asset_id}/access")
def admin_farmer_media_access_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    admin_service.require_admin(context)
    asset = repo.get_media_asset(media_asset_id)
    if asset is None or asset.get("upload_status") != "READY":
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if str(asset.get("storage_backend") or "LOCAL").upper() == "LOCAL":
        return {
            "url": f"/v1/crop-observations/admin/media/{media_asset_id}/content",
            "external": False,
            "expires_in_seconds": None,
        }
    return {
        "url": s3_storage.create_download_url(object_key=asset["object_key"]),
        "external": True,
        "expires_in_seconds": settings.s3_presigned_download_ttl_seconds,
    }


@router.get("/media/{media_asset_id}/content")
def admin_farmer_media_content_endpoint(
    media_asset_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    admin_service.require_admin(context)
    asset = repo.get_media_asset(media_asset_id)
    if asset is None or asset.get("upload_status") != "READY":
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if str(asset.get("storage_backend") or "LOCAL").upper() == "LOCAL":
        return Response(
            content=local_storage.read_bytes(object_key=asset["object_key"]),
            media_type=asset["mime_type"],
        )
    return RedirectResponse(
        url=s3_storage.create_download_url(object_key=asset["object_key"]),
        status_code=307,
    )


@router.post("/system-media/uploads", response_model=SystemMediaUploadResponse, status_code=201)
def request_system_media_upload_endpoint(
    payload: SystemMediaUploadRequest,
    context: RequestContext = Depends(get_request_context),
):
    return svc.request_system_media_upload(context, payload)


@router.put("/system-media/local-content/{asset_id}", status_code=204)
async def upload_local_system_media_endpoint(
    asset_id: UUID,
    request: Request,
    context: RequestContext = Depends(get_request_context),
):
    data = await request.body()
    svc.write_local_system_media(context, asset_id, data)
    return Response(status_code=204)


@router.post("/system-media/{asset_id}/complete", response_model=SystemMediaCompleteResponse)
def complete_system_media_endpoint(
    asset_id: UUID,
    target_type: Literal["CROP", "STAGE", "STAGE_PRACTICE", "FIELD_OPTION"] = Query(...),
    target_id: UUID = Query(...),
    asset_role: Literal[
        "CROP_CARD_IMAGE",
        "STAGE_IMAGE",
        "INSTRUCTION_AUDIO",
        "PRACTICE_GUIDE_IMAGE",
        "OPTION_IMAGE",
    ] = Query(...),
    locale: str | None = Query(default=None),
    slot_number: int | None = Query(default=None, ge=1, le=10),
    context: RequestContext = Depends(get_request_context),
):
    return svc.complete_system_media_upload(
        context,
        asset_id=asset_id,
        target_type=target_type,
        target_id=target_id,
        asset_role=asset_role,
        locale=locale,
        slot_number=slot_number,
    )


@router.get("/system-media", response_model=list[SystemMediaBindingOut])
def list_system_media_endpoint(
    target_type: str | None = Query(default=None),
    target_id: UUID | None = Query(default=None),
    asset_role: str | None = Query(default=None),
    locale: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    context: RequestContext = Depends(get_request_context),
):
    return svc.list_system_media(
        context,
        target_type=target_type,
        target_id=target_id,
        asset_role=asset_role,
        locale=locale,
        limit=limit,
    )


@router.delete("/system-media/bindings/{binding_id}", status_code=204)
def delete_system_media_binding_endpoint(
    binding_id: UUID,
    context: RequestContext = Depends(get_request_context),
):
    svc.delete_system_media_binding(context, binding_id)
    return Response(status_code=204)


@router.post("/configurations/{config_version_id}/generate-audio", response_model=TtsBatchOut)
def generate_configuration_audio_endpoint(
    config_version_id: UUID,
    payload: TtsBatchRequest,
    context: RequestContext = Depends(get_request_context),
):
    return svc.generate_config_audio(
        context,
        config_version_id=config_version_id,
        locales=payload.locales,
        force=payload.force,
    )


@router.get("/system/status", response_model=AdminSystemStatusOut)
def system_status_endpoint(context: RequestContext = Depends(get_request_context)):
    return svc.get_system_status(context)
