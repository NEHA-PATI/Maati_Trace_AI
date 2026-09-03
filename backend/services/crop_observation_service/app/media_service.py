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
from services.crop_observation_service.app.storage import active_backend, is_local

_MEDIA_ROLE_BY_TYPE = {"IMAGE": "PHOTO", "AUDIO": "VOICE_NOTE"}
_EXTENSION_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
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


def _resolve_media_policy(owner_type: str, owner_ctx: dict, payload: MediaUploadRequest) -> tuple[str, int, int | None]:
    from shared.config.settings import settings

    media_role = _MEDIA_ROLE_BY_TYPE[payload.media_type]
    if owner_type == "DAILY_STAGE":
        if media_role == "PHOTO":
            if payload.media_purpose not in {"GENERAL", "CROP_CONDITION"}:
                raise CropObservationError("INVALID_MEDIA_PURPOSE", "Stage photos must describe crop condition.", 422)
            purpose = "CROP_CONDITION"
            limit = settings.max_images_per_owner
            max_seconds = None
        else:
            if payload.media_purpose != "GENERAL":
                raise CropObservationError("INVALID_MEDIA_PURPOSE", "Voice notes use the GENERAL purpose.", 422)
            purpose = "GENERAL"
            limit = settings.max_audio_per_owner
            max_seconds = settings.max_audio_duration_seconds
        return purpose, limit, max_seconds

    practice = repo.get_practice_observation(payload.owner_id)
    if practice is None:
        raise CropObservationError("OBSERVATION_NOT_FOUND", "Observation was not found.", 404)
    stage_practice = repo.get_stage_practice(practice["stage_practice_id"])
    media_config = (stage_practice or {}).get("media_config") or {}
    voice_note = media_config.get("voice_note") or {}
    issue = media_config.get("issue_evidence") or {}
    practice_evidence = media_config.get("practice_evidence") or {}

    if media_role == "PHOTO":
        if payload.media_purpose == "GENERAL":
            payload.media_purpose = "PRACTICE_EVIDENCE"
        if payload.media_purpose == "ISSUE_EVIDENCE":
            if not issue.get("enabled", False):
                raise CropObservationError("MEDIA_PURPOSE_DISABLED", "Issue evidence is not enabled for this practice.", 422)
            return "ISSUE_EVIDENCE", int(issue.get("max_images", settings.max_images_per_owner)), None
        if payload.media_purpose == "PRACTICE_EVIDENCE":
            if not practice_evidence.get("enabled", True):
                raise CropObservationError("MEDIA_PURPOSE_DISABLED", "Practice evidence is not enabled for this practice.", 422)
            return "PRACTICE_EVIDENCE", int(practice_evidence.get("max_images", settings.max_images_per_owner)), None
        raise CropObservationError("INVALID_MEDIA_PURPOSE", "This image purpose is not valid for practice evidence.", 422)

    if payload.media_purpose != "GENERAL":
        raise CropObservationError("INVALID_MEDIA_PURPOSE", "Voice notes use the GENERAL purpose.", 422)
    if not voice_note.get("enabled", True):
        raise CropObservationError("MEDIA_PURPOSE_DISABLED", "Voice notes are not enabled for this practice.", 422)
    return "GENERAL", int(voice_note.get("max_count", settings.max_audio_per_owner)), int(
        voice_note.get("max_seconds", settings.max_audio_duration_seconds)
    )


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
    media_purpose, limit, max_seconds = _resolve_media_policy(payload.owner_type, owner_ctx, payload)
    if max_seconds is not None and payload.duration_seconds and payload.duration_seconds > max_seconds:
        raise CropObservationError("MEDIA_TOO_LONG", "Audio exceeds the duration limit for this entry.", 422)

    existing_count = repo.count_owner_media_by_purpose(
        payload.owner_type,
        payload.owner_id,
        media_role,
        media_purpose,
    )
    if existing_count >= limit:
        raise CropObservationError(
            "MEDIA_LIMIT_REACHED",
            f"Maximum {limit} {media_role.lower()} attachment(s) reached for this entry.",
            409,
        )
    slot_number = (
        repo.next_owner_media_slot(payload.owner_type, payload.owner_id, media_role, media_purpose)
        if media_role == "PHOTO"
        else None
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

    bucket_name = "local" if is_local() else settings.crop_observation_s3_bucket
    asset = repo.create_media_asset(
        owner_user_id=context.principal.user_id,
        bucket_name=bucket_name,
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
        media_purpose=media_purpose,
        slot_number=slot_number,
    )

    presign = active_backend().create_upload_url(object_key=object_key, mime_type=payload.mime_type)
    return MediaUploadResponse(
        media_asset_id=asset["media_asset_id"],
        upload_url=presign["upload_url"],
        method=presign["method"],
        headers=presign["headers"],
        expires_in_seconds=presign["expires_in_seconds"],
    )


def write_local_media_content(context: RequestContext, media_asset_id: UUID, data: bytes) -> None:
    """Receive the raw bytes for a LOCAL-backend upload (the browser PUTs
    here instead of straight to S3 — see storage/local.py create_upload_url).
    Validates ownership, size, MIME-declared type and, for images, that the
    bytes actually decode as an image before writing them to disk."""
    from PIL import Image, UnidentifiedImageError

    from shared.config.settings import settings

    asset = repo.get_media_asset(media_asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if asset["owner_user_id"] != context.principal.user_id:
        raise CropObservationError("MEDIA_ACCESS_FORBIDDEN", "You cannot upload this media.", 403)
    if asset["upload_status"] == "READY":
        raise CropObservationError("MEDIA_ALREADY_UPLOADED", "This media was already uploaded.", 409)

    max_bytes = settings.max_image_bytes if asset["media_type"] == "IMAGE" else settings.max_audio_bytes
    if len(data) > max_bytes:
        raise CropObservationError("MEDIA_TOO_LARGE", "File exceeds the size limit.", 422)

    if asset["media_type"] == "IMAGE":
        import io

        try:
            Image.open(io.BytesIO(data)).verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise CropObservationError("INVALID_MEDIA_FILE", "This does not look like a valid image.", 422) from exc

    from services.crop_observation_service.app.storage import local as local_storage

    local_storage.write_bytes(object_key=asset["object_key"], data=data)


def complete_media_upload(context: RequestContext, media_asset_id: UUID) -> MediaAssetResponse:
    asset = repo.get_media_asset(media_asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if asset["owner_user_id"] != context.principal.user_id:
        raise CropObservationError("MEDIA_ACCESS_FORBIDDEN", "You cannot finalize this media.", 403)

    head = active_backend().head_object(object_key=asset["object_key"])
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
        content_url=f"/v1/crop-observations/media/{row['media_asset_id']}/content",
    )


def get_media_content(context: RequestContext, media_asset_id: UUID) -> tuple[bytes, str]:
    """Stream a farmer's own media back — used for replaying a previous
    voice note or opening a previous photo (fetched on demand, never
    preloaded — see PreviousEntryRow.jsx)."""
    from services.crop_observation_service.app.storage import local as local_storage

    asset = repo.get_media_asset(media_asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if asset["owner_user_id"] != context.principal.user_id:
        raise CropObservationError("MEDIA_ACCESS_FORBIDDEN", "You cannot view this media.", 403)
    if not is_local():
        raise CropObservationError(
            "MEDIA_CONTENT_NOT_LOCAL",
            "This media is stored remotely — use its presigned URL instead.",
            409,
        )
    return local_storage.read_bytes(object_key=asset["object_key"]), asset["mime_type"]
