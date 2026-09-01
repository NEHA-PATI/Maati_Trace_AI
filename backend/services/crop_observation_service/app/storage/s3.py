from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from shared.config.settings import settings
from services.crop_observation_service.app.errors import CropObservationError


@lru_cache
def _client():
    if not settings.crop_observation_s3_bucket:
        raise CropObservationError(
            "MEDIA_STORAGE_NOT_CONFIGURED",
            "Media uploads are not configured on this environment yet.",
            503,
        )
    # Deliberately no AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY here — boto3's
    # default credential chain resolves an IAM role in production, or an
    # AWS_PROFILE / local credentials file in development. See
    # services/crop_observation_service/.env.example.
    return boto3.client("s3", region_name=settings.aws_region)


def create_upload_url(*, object_key: str, mime_type: str) -> dict[str, object]:
    try:
        url = _client().generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.crop_observation_s3_bucket,
                "Key": object_key,
                "ContentType": mime_type,
            },
            ExpiresIn=settings.s3_presigned_upload_ttl_seconds,
        )
    except (BotoCoreError, ClientError) as exc:
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    return {
        "upload_url": url,
        "method": "PUT",
        "headers": {"Content-Type": mime_type},
        "expires_in_seconds": settings.s3_presigned_upload_ttl_seconds,
    }


def create_download_url(*, object_key: str) -> str:
    try:
        return _client().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.crop_observation_s3_bucket,
                "Key": object_key,
            },
            ExpiresIn=settings.s3_presigned_download_ttl_seconds,
        )
    except (BotoCoreError, ClientError) as exc:
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc


def head_object(*, object_key: str) -> dict[str, object] | None:
    try:
        return _client().head_object(Bucket=settings.crop_observation_s3_bucket, Key=object_key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchKey", "NotFound"):
            return None
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc
    except BotoCoreError as exc:
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc
