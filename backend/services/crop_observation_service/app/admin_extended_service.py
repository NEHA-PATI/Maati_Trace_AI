from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from shared.config.settings import settings
from services.crop_observation_service.app import (
    admin_extended_repository as xrepo,
    admin_service,
    repository as repo,
    tts_service,
)
from services.crop_observation_service.app.admin_extended_schemas import (
    AdminOverviewOut,
    AdminPracticeRecordOut,
    AdminRecordDetailOut,
    AdminRecordMediaOut,
    AdminSystemStatusOut,
    RecordReviewOut,
    RecordReviewUpdateRequest,
    SystemMediaBindingOut,
    SystemMediaCompleteResponse,
    SystemMediaUploadRequest,
    SystemMediaUploadResponse,
    TtsBatchItemOut,
    TtsBatchOut,
)
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.storage import active_backend, backend_for, is_local


_ROLE_TARGET = {
    "CROP_CARD_IMAGE": "CROP",
    "STAGE_IMAGE": "STAGE",
    "INSTRUCTION_AUDIO": "STAGE",
    "PRACTICE_GUIDE_IMAGE": "STAGE_PRACTICE",
    "OPTION_IMAGE": "FIELD_OPTION",
}
_IMAGE_ROLES = {"CROP_CARD_IMAGE", "STAGE_IMAGE", "PRACTICE_GUIDE_IMAGE", "OPTION_IMAGE"}
_AUDIO_ROLES = {"INSTRUCTION_AUDIO"}
_EXTENSION_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
}


def _admin(context: RequestContext) -> None:
    admin_service.require_admin(context)


def get_overview(
    context: RequestContext,
    *,
    from_date: date | None,
    to_date: date | None,
) -> AdminOverviewOut:
    _admin(context)
    values = xrepo.get_overview(from_date=from_date, to_date=to_date)
    values["by_crop"] = xrepo.overview_by_crop(from_date=from_date, to_date=to_date)
    values["by_practice"] = xrepo.overview_by_practice(from_date=from_date, to_date=to_date)
    values["trend"] = xrepo.overview_trend(from_date=from_date, to_date=to_date)
    return AdminOverviewOut(**values)


def list_records(context: RequestContext, **filters) -> list[AdminPracticeRecordOut]:
    _admin(context)
    return [AdminPracticeRecordOut(**row) for row in xrepo.list_records(**filters)]


def get_record(context: RequestContext, record_id: UUID) -> AdminRecordDetailOut:
    _admin(context)
    row = xrepo.get_record(record_id)
    if row is None:
        raise CropObservationError("RECORD_NOT_FOUND", "This crop observation record was not found.", 404)
    media = [
        AdminRecordMediaOut(
            **item,
            content_url=f"/v1/crop-observations/admin/media/{item['media_asset_id']}/content",
        )
        for item in xrepo.get_record_media(record_id)
    ]
    return AdminRecordDetailOut(
        **row,
        media=media,
        revisions=xrepo.get_record_revisions(record_id),
    )


def update_review(
    context: RequestContext,
    record_id: UUID,
    payload: RecordReviewUpdateRequest,
) -> RecordReviewOut:
    _admin(context)
    before = xrepo.get_record(record_id)
    if before is None:
        raise CropObservationError("RECORD_NOT_FOUND", "This crop observation record was not found.", 404)
    row = xrepo.upsert_record_review(
        record_id=record_id,
        review_status=payload.review_status,
        admin_note=payload.admin_note,
        reviewed_by_user_id=context.principal.user_id,
    )
    xrepo.upsert_audit(
        actor_user_id=context.principal.user_id,
        action="REVIEW_UPDATED",
        entity_type="PRACTICE_RECORD",
        entity_id=record_id,
        before_state={"review_status": before.get("review_status"), "admin_note": before.get("admin_note")},
        after_state={"review_status": payload.review_status, "admin_note": payload.admin_note},
        correlation_id=context.correlation_id,
    )
    return RecordReviewOut(**row)


def list_issues(context: RequestContext, *, limit: int, offset: int) -> list[AdminPracticeRecordOut]:
    _admin(context)
    return [AdminPracticeRecordOut(**row) for row in xrepo.list_issues(limit=limit, offset=offset)]


def _validate_system_media(payload: SystemMediaUploadRequest) -> None:
    expected_target = _ROLE_TARGET[payload.asset_role]
    if payload.target_type != expected_target:
        raise CropObservationError(
            "INVALID_MEDIA_BINDING",
            f"{payload.asset_role} must target {expected_target}.",
            422,
        )
    if not xrepo.target_exists(payload.target_type, payload.target_id):
        raise CropObservationError("MEDIA_TARGET_NOT_FOUND", "The media target was not found.", 404)
    if payload.target_type != "CROP":
        config = xrepo.configuration_for_target(payload.target_type, payload.target_id)
        if config is None:
            raise CropObservationError("MEDIA_TARGET_NOT_FOUND", "The media target was not found.", 404)
        if config["status"] != "DRAFT":
            raise CropObservationError(
                "CONFIGURATION_IMMUTABLE",
                "Published configuration content cannot be changed.",
                409,
            )

    if payload.asset_role in _IMAGE_ROLES:
        if payload.mime_type not in settings.allowed_image_mime_types_list:
            raise CropObservationError("UNSUPPORTED_MEDIA_TYPE", "Unsupported image type.", 422)
        if payload.byte_size > settings.max_image_bytes:
            raise CropObservationError("MEDIA_TOO_LARGE", "Image exceeds the size limit.", 422)
        if payload.locale is not None:
            raise CropObservationError("LOCALE_NOT_ALLOWED", "Images do not require a locale.", 422)
    elif payload.asset_role in _AUDIO_ROLES:
        if payload.mime_type not in settings.allowed_audio_mime_types_list:
            raise CropObservationError("UNSUPPORTED_MEDIA_TYPE", "Unsupported audio type.", 422)
        if payload.byte_size > settings.max_audio_bytes:
            raise CropObservationError("MEDIA_TOO_LARGE", "Audio exceeds the size limit.", 422)
        if not payload.locale or payload.locale not in settings.allowed_locales_list:
            raise CropObservationError("INVALID_LOCALE", "Instruction audio requires en-IN or or-IN.", 422)
        if (
            payload.duration_seconds is not None
            and payload.duration_seconds > settings.max_instruction_audio_duration_seconds
        ):
            raise CropObservationError("MEDIA_TOO_LONG", "Instruction audio exceeds the duration limit.", 422)


def request_system_media_upload(
    context: RequestContext,
    payload: SystemMediaUploadRequest,
) -> SystemMediaUploadResponse:
    _admin(context)
    _validate_system_media(payload)

    ext = _EXTENSION_BY_MIME.get(payload.mime_type)
    if not ext:
        raise CropObservationError("UNSUPPORTED_MEDIA_TYPE", "Unsupported media type.", 422)
    token = uuid4()
    locale_segment = payload.locale or "neutral"
    object_key = (
        f"system/uploads/{payload.target_type.lower()}/{payload.target_id}/"
        f"{payload.asset_role.lower()}/{locale_segment}/{token}.{ext}"
    )
    asset = repo.create_system_media_asset(
        asset_type=payload.asset_role,
        crop_id=None,
        stage_id=None,
        bucket_name="local" if is_local() else settings.crop_observation_s3_bucket,
        object_key=object_key,
        mime_type=payload.mime_type,
        byte_size=payload.byte_size,
        locale=payload.locale,
        duration_seconds=payload.duration_seconds,
        storage_backend=settings.media_storage_backend.upper(),
        original_filename=payload.original_filename,
        upload_status="REQUESTED",
        created_by_user_id=context.principal.user_id,
        is_active=False,
        upload_expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.s3_presigned_upload_ttl_seconds),
    )
    presign = active_backend().create_upload_url(
        object_key=object_key,
        mime_type=payload.mime_type,
        system_asset_id=asset["asset_id"],
    )
    # Target data is not written to the binding until the object has been
    # verified. The frontend sends the same target metadata on complete.
    xrepo.upsert_audit(
        actor_user_id=context.principal.user_id,
        action="SYSTEM_MEDIA_UPLOAD_REQUESTED",
        entity_type=payload.asset_role,
        entity_id=asset["asset_id"],
        before_state=None,
        after_state={
            "target_type": payload.target_type,
            "target_id": str(payload.target_id),
            "asset_role": payload.asset_role,
            "locale": payload.locale,
            "slot_number": payload.slot_number,
        },
        correlation_id=context.correlation_id,
    )
    return SystemMediaUploadResponse(
        asset_id=asset["asset_id"],
        upload_url=presign["upload_url"],
        method=presign["method"],
        headers=presign["headers"],
        expires_in_seconds=presign["expires_in_seconds"],
    )


def write_local_system_media(
    context: RequestContext,
    asset_id: UUID,
    data: bytes,
) -> None:
    _admin(context)
    asset = repo.get_system_media_asset_any_status(asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if str(asset.get("storage_backend") or "LOCAL").upper() != "LOCAL":
        raise CropObservationError("LOCAL_UPLOAD_NOT_ALLOWED", "This asset is not a local upload.", 409)
    if asset.get("created_by_user_id") and asset["created_by_user_id"] != context.principal.user_id:
        raise CropObservationError("MEDIA_ACCESS_FORBIDDEN", "You cannot upload this media.", 403)
    if len(data) != int(asset["byte_size"]):
        raise CropObservationError("MEDIA_SIZE_MISMATCH", "The file size does not match the upload request.", 422)

    if str(asset["mime_type"]).startswith("image/"):
        import io
        from PIL import Image, UnidentifiedImageError

        try:
            Image.open(io.BytesIO(data)).verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise CropObservationError("INVALID_MEDIA_FILE", "This does not look like a valid image.", 422) from exc

    backend_for("LOCAL").write_bytes(object_key=asset["object_key"], data=data)


def complete_system_media_upload(
    context: RequestContext,
    *,
    asset_id: UUID,
    target_type: str,
    target_id: UUID,
    asset_role: str,
    locale: str | None,
    slot_number: int | None,
) -> SystemMediaCompleteResponse:
    _admin(context)
    expected_target = _ROLE_TARGET.get(asset_role)
    if expected_target is None or target_type != expected_target:
        raise CropObservationError("INVALID_MEDIA_BINDING", "Invalid media target/role combination.", 422)
    if not xrepo.target_exists(target_type, target_id):
        raise CropObservationError("MEDIA_TARGET_NOT_FOUND", "The media target was not found.", 404)
    if target_type != "CROP":
        config = xrepo.configuration_for_target(target_type, target_id)
        if config is None:
            raise CropObservationError("MEDIA_TARGET_NOT_FOUND", "The media target was not found.", 404)
        if config["status"] != "DRAFT":
            raise CropObservationError(
                "CONFIGURATION_IMMUTABLE",
                "Published configuration content cannot be changed.",
                409,
            )

    asset = repo.get_system_media_asset_any_status(asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)

    # Do not allow the second phase of the upload to change the semantic role
    # or locale that was declared in phase 1. That would make a presigned URL
    # reusable for a different configuration target.
    if asset.get("asset_type") != asset_role:
        raise CropObservationError(
            "MEDIA_ROLE_MISMATCH",
            "The completed media role does not match the upload request.",
            422,
        )
    if (asset.get("locale") or None) != (locale or None):
        raise CropObservationError(
            "MEDIA_LOCALE_MISMATCH",
            "The completed media locale does not match the upload request.",
            422,
        )
    if asset.get("created_by_user_id") and asset["created_by_user_id"] != context.principal.user_id:
        raise CropObservationError("MEDIA_ACCESS_FORBIDDEN", "You cannot complete this media upload.", 403)

    if asset["upload_status"] == "READY":
        # Idempotent completion still re-establishes the requested binding.
        pass
    storage = backend_for(asset.get("storage_backend"))
    head = storage.head_object(object_key=asset["object_key"])
    if head is None:
        raise CropObservationError("MEDIA_UPLOAD_NOT_FOUND", "Upload the file before completing it.", 409)
    if int(head.get("ContentLength") or -1) != int(asset["byte_size"]):
        raise CropObservationError("MEDIA_SIZE_MISMATCH", "The uploaded file size does not match.", 422)
    content_type = head.get("ContentType")
    if content_type and str(content_type).split(";", 1)[0].lower() != str(asset["mime_type"]).lower():
        raise CropObservationError("MEDIA_TYPE_MISMATCH", "The uploaded file type does not match.", 422)

    repo.mark_system_media_ready(asset_id)
    binding = repo.activate_system_media_binding(
        asset_id=asset_id,
        target_type=target_type,
        target_id=target_id,
        asset_role=asset_role,
        locale=locale,
        slot_number=slot_number,
    )
    xrepo.upsert_audit(
        actor_user_id=context.principal.user_id,
        action="SYSTEM_MEDIA_ACTIVATED",
        entity_type=asset_role,
        entity_id=asset_id,
        before_state=None,
        after_state={
            "target_type": target_type,
            "target_id": str(target_id),
            "locale": locale,
            "binding_id": str(binding["binding_id"]),
        },
        correlation_id=context.correlation_id,
    )
    out = SystemMediaBindingOut(
        **binding,
        mime_type=asset["mime_type"],
        byte_size=asset["byte_size"],
        duration_seconds=asset.get("duration_seconds"),
        storage_backend=asset.get("storage_backend"),
        object_key=asset.get("object_key"),
        upload_status="READY",
        original_filename=asset.get("original_filename"),
        content_url=f"/v1/crop-observations/system-media/{asset_id}/content",
    )
    return SystemMediaCompleteResponse(
        asset_id=asset_id,
        binding=out,
        content_url=f"/v1/crop-observations/system-media/{asset_id}/content",
    )


def list_system_media(context: RequestContext, **filters) -> list[SystemMediaBindingOut]:
    _admin(context)
    rows = repo.list_system_media_bindings(**filters)
    return [
        SystemMediaBindingOut(
            **row,
            content_url=f"/v1/crop-observations/system-media/{row['asset_id']}/content",
        )
        for row in rows
    ]


def delete_system_media_binding(context: RequestContext, binding_id: UUID) -> None:
    _admin(context)
    existing = repo.get_system_media_binding(binding_id)
    if existing is None:
        raise CropObservationError("MEDIA_BINDING_NOT_FOUND", "Media binding was not found.", 404)
    if existing["target_type"] != "CROP":
        config = xrepo.configuration_for_target(existing["target_type"], existing["target_id"])
        if config is None or config["status"] != "DRAFT":
            raise CropObservationError(
                "CONFIGURATION_IMMUTABLE",
                "Published configuration content cannot be changed.",
                409,
            )
    row = repo.deactivate_system_media_binding(binding_id)
    if row is None:
        raise CropObservationError("MEDIA_BINDING_NOT_FOUND", "Media binding was not found.", 404)
    if row["target_type"] != "CROP":
        config = xrepo.configuration_for_target(row["target_type"], row["target_id"])
        if config is None or config["status"] != "DRAFT":
            raise CropObservationError(
                "CONFIGURATION_IMMUTABLE",
                "Published configuration content cannot be changed.",
                409,
            )
    xrepo.upsert_audit(
        actor_user_id=context.principal.user_id,
        action="SYSTEM_MEDIA_BINDING_DEACTIVATED",
        entity_type=row["asset_role"],
        entity_id=row["asset_id"],
        before_state={"binding_id": str(binding_id), "is_active": True},
        after_state={"binding_id": str(binding_id), "is_active": False},
        correlation_id=context.correlation_id,
    )


def generate_config_audio(
    context: RequestContext,
    *,
    config_version_id: UUID,
    locales: list[str],
    force: bool,
) -> TtsBatchOut:
    _admin(context)
    config = repo.get_config_version(config_version_id)
    if config is None:
        raise CropObservationError("CONFIGURATION_NOT_FOUND", "This configuration was not found.", 404)
    if config["status"] != "DRAFT":
        raise CropObservationError(
            "CONFIGURATION_IMMUTABLE",
            "Published configuration content cannot be changed.",
            409,
        )
    for locale in locales:
        if locale not in settings.allowed_locales_list:
            raise CropObservationError("INVALID_LOCALE", "Unsupported crop-observation locale.", 422)
    items: list[TtsBatchItemOut] = []
    for stage_id in xrepo.list_stage_ids_for_config(config_version_id):
        for locale in locales:
            try:
                result = tts_service.generate_instruction_audio(
                    context,
                    stage_id=stage_id,
                    locale=locale,
                    force=force,
                )
                items.append(
                    TtsBatchItemOut(
                        stage_id=stage_id,
                        locale=locale,
                        status=result.status,
                        asset_id=result.asset_id,
                    )
                )
            except CropObservationError as exc:
                items.append(
                    TtsBatchItemOut(
                        stage_id=stage_id,
                        locale=locale,
                        status="FAILED",
                        error_code=exc.code,
                        error_message=exc.message,
                    )
                )
    return TtsBatchOut(
        total=len(items),
        ready=sum(1 for item in items if item.status == "READY"),
        failed=sum(1 for item in items if item.status != "READY"),
        items=items,
    )


def get_system_status(context: RequestContext) -> AdminSystemStatusOut:
    _admin(context)
    counts = xrepo.system_counts()
    return AdminSystemStatusOut(
        service="crop_observation_service",
        environment=settings.app_env,
        storage_backend=settings.media_storage_backend.upper(),
        s3_bucket_configured=bool(settings.crop_observation_s3_bucket),
        s3_bucket=settings.crop_observation_s3_bucket or None,
        tts_enabled=settings.cartesia_tts_enabled,
        cartesia_key_configured=bool(settings.cartesia_api_key),
        tts_model=settings.cartesia_tts_model,
        **counts,
    )
