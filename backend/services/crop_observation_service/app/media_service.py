from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from services.crop_observation_service.app import observation_service, repository as repo
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.schemas import (
    MediaAssetResponse,
    MediaUploadRequest,
    MediaUploadResponse,
)
from services.crop_observation_service.app.storage import s3 as s3_storage

_MEDIA_ROLE_BY_TYPE = {"IMAGE": "PHOTO", "AUDIO": "VOICE_NOTE"}
_EXTENSION_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
}


def _resolve_owner_context(owner_type: str, owner_id: UUID) -> dict:
    """Resolve a media owner (a daily status row or a practice observation
    row) back to its crop_cycle -> farm_crop -> farm, so we can both
    authorize the caller and build a stable S3 object key."""
    if owner_type == "DAILY_STAGE":
        daily = repo.get_daily_observation(owner_id)
        if daily is None:
            raise CropObservationError("OBSERVATION_NOT_FOUND", "Observation was not found.", 404)
    else:
        practice = repo.get_practice_observation(owner_id)
        if practice is None:
            raise CropObservationError("OBSERVATION_NOT_FOUND", "Observation was not found.", 404)
        daily = repo.get_daily_observation(practice["daily_observation_id"])
        if daily is None:
            raise CropObservationError("OBSERVATION_NOT_FOUND", "Observation was not found.", 404)

    cycle = repo.get_crop_cycle(daily["crop_cycle_id"])
    farm_crop = repo.get_farm_crop(cycle["farm_crop_id"])
    return {"daily": daily, "cycle": cycle, "farm_crop": farm_crop}


def _validate_media_limits(*, payload: MediaUploadRequest) -> None:
    from shared.config.settings import settings

    if payload.media_type == "IMAGE":
        if payload.mime_type not in settings.allowed_image_mime_types_list:
            raise CropObservationError("UNSUPPORTED_MEDIA_TYPE", "Unsupported image type.", 422)
        if payload.byte_size > settings.max_image_bytes:
            raise CropObservationError("MEDIA_TOO_LARGE", "Image exceeds the size limit.", 422)
    else:
        if payload.mime_type not in settings.allowed_audio_mime_types_list:
            raise CropObservationError("UNSUPPORTED_MEDIA_TYPE", "Unsupported audio type.", 422)
        if payload.byte_size > settings.max_audio_bytes:
            raise CropObservationError("MEDIA_TOO_LARGE", "Audio exceeds the size limit.", 422)
        if (
            payload.duration_seconds is not None
            and payload.duration_seconds > settings.max_audio_duration_seconds
        ):
            raise CropObservationError("MEDIA_TOO_LONG", "Audio exceeds the duration limit.", 422)


def request_media_upload(
    context: RequestContext,
    payload: MediaUploadRequest,
) -> MediaUploadResponse:
    from shared.config.settings import settings

    _validate_media_limits(payload=payload)

    owner_ctx = _resolve_owner_context(payload.owner_type, payload.owner_id)
    farm_crop = owner_ctx["farm_crop"]
    cycle = owner_ctx["cycle"]
    daily = owner_ctx["daily"]

    # Reuses the same farm_registry_service authorization every write goes
    # through — the caller must actually be allowed to act on this farm.
    observation_service.resolve_cycle_and_authorize(context, cycle["crop_cycle_id"])

    media_role = _MEDIA_ROLE_BY_TYPE[payload.media_type]
    limit = settings.max_images_per_owner if media_role == "PHOTO" else settings.max_audio_per_owner
    existing_count = repo.count_owner_media(payload.owner_type, payload.owner_id, media_role)
    if existing_count >= limit:
        raise CropObservationError(
            "MEDIA_LIMIT_REACHED",
            f"Maximum {limit} {media_role.lower()} attachment(s) reached for this entry.",
            409,
        )

    extension = _EXTENSION_BY_MIME.get(payload.mime_type, "bin")
    media_uuid = uuid4()
    today = datetime.utcnow()
    kind = "images" if payload.media_type == "IMAGE" else "audio"
    owner_segment = (
        f"daily/{daily['daily_observation_id']}"
        if payload.owner_type == "DAILY_STAGE"
        else f"practice/{payload.owner_id}"
    )
    object_key = (
        f"farmer/{farm_crop['farmer_user_id']}/farm/{farm_crop['farm_id']}/"
        f"crop-cycle/{cycle['crop_cycle_id']}/{today:%Y/%m/%d}/{owner_segment}/"
        f"{kind}/{media_uuid}.{extension}"
    )

    asset = repo.create_media_asset(
        owner_user_id=context.principal.user_id,
        bucket_name=settings.crop_observation_s3_bucket,
        object_key=object_key,
        media_type=payload.media_type,
        mime_type=payload.mime_type,
        byte_size=payload.byte_size,
        duration_seconds=payload.duration_seconds,
    )
    repo.create_observation_media(
        owner_type=payload.owner_type,
        owner_id=payload.owner_id,
        media_asset_id=asset["media_asset_id"],
        media_role=media_role,
    )

    presign = s3_storage.create_upload_url(object_key=object_key, mime_type=payload.mime_type)
    return MediaUploadResponse(
        media_asset_id=asset["media_asset_id"],
        upload_url=presign["upload_url"],
        method=presign["method"],
        headers=presign["headers"],
        expires_in_seconds=presign["expires_in_seconds"],
    )


def complete_media_upload(context: RequestContext, media_asset_id: UUID) -> MediaAssetResponse:
    asset = repo.get_media_asset(media_asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if asset["owner_user_id"] != context.principal.user_id:
        raise CropObservationError("MEDIA_ACCESS_FORBIDDEN", "You cannot finalize this media.", 403)

    head = s3_storage.head_object(object_key=asset["object_key"])
    if head is None:
        raise CropObservationError(
            "MEDIA_UPLOAD_NOT_FOUND",
            "The file was not found in storage — upload it before completing.",
            409,
        )

    content_length = head.get("ContentLength")
    if content_length is not None and int(content_length) != int(asset["byte_size"]):
        raise CropObservationError(
            "MEDIA_SIZE_MISMATCH",
            "The uploaded file size does not match what was declared.",
            422,
        )

    row = repo.mark_media_ready(media_asset_id)
    return MediaAssetResponse(
        media_asset_id=row["media_asset_id"],
        media_type=row["media_type"],
        mime_type=row["mime_type"],
        byte_size=row["byte_size"],
        duration_seconds=row["duration_seconds"],
        upload_status=row["upload_status"],
    )
