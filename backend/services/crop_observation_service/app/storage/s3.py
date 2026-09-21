from __future__ import annotations

from functools import lru_cache
from uuid import UUID

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
    # Production: use the platform IAM role. Local development can use
    # AWS_PROFILE or the normal AWS credentials chain. No access key is
    # hard-coded in this service.
    return boto3.client("s3", region_name=settings.aws_region)


def create_upload_url(
    *,
    object_key: str,
    mime_type: str,
    media_asset_id: UUID | None = None,
    system_asset_id: UUID | None = None,
) -> dict[str, object]:
    del media_asset_id, system_asset_id  # only LOCAL needs these ids in the URL
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


def put_bytes(*, object_key: str, data: bytes, mime_type: str) -> int:
    try:
        _client().put_object(
            Bucket=settings.crop_observation_s3_bucket,
            Key=object_key,
            Body=data,
            ContentType=mime_type,
            ServerSideEncryption="AES256",
        )
        return len(data)
    except (BotoCoreError, ClientError) as exc:
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc


def head_object(*, object_key: str) -> dict[str, object] | None:
    try:
        return _client().head_object(
            Bucket=settings.crop_observation_s3_bucket,
            Key=object_key,
        )
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


def read_bytes(*, object_key: str) -> bytes:
    try:
        response = _client().get_object(Bucket=settings.crop_observation_s3_bucket, Key=object_key)
        return response["Body"].read()
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            raise CropObservationError("MEDIA_FILE_MISSING", "Media file was not found.", 404) from exc
        raise CropObservationError("MEDIA_STORAGE_UNAVAILABLE", "Media storage is temporarily unavailable.", 503, internal_message=str(exc)) from exc
    except BotoCoreError as exc:
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc


def delete(*, object_key: str) -> None:
    try:
        _client().delete_object(
            Bucket=settings.crop_observation_s3_bucket,
            Key=object_key,
        )
    except (BotoCoreError, ClientError) as exc:
        raise CropObservationError(
            "MEDIA_STORAGE_UNAVAILABLE",
            "Media storage is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc
