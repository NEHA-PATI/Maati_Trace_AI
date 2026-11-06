from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, Response

from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.storage import local as local_storage
from services.crop_observation_service.app.storage import s3 as s3_storage
from shared.config.settings import settings

router = APIRouter(prefix="/v1/crop-observations/system-media", tags=["system-media"])


@router.get("/{asset_id}/content")
def get_system_media_content_endpoint(asset_id: UUID):
    """Serve curated crop/stage/option media through a stable service URL.

    LOCAL: stream bytes from disk.
    S3: issue a short-lived 307 redirect to a private presigned GET URL.

    The farmer frontend therefore never changes when the environment flips
    from LOCAL to S3.
    """
    asset = repo.get_system_media_asset(asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)

    if str(asset.get("storage_backend") or "LOCAL").upper() == "LOCAL":
        try:
            data = local_storage.read_bytes(object_key=asset["object_key"])
            return Response(content=data, media_type=asset["mime_type"])
        except CropObservationError as exc:
            # During the LOCAL -> S3 migration, old rows can still say LOCAL
            # while their object has already been copied to S3. Read the
            # durable copy when it exists; do not mask a real storage error.
            if (
                exc.code != "MEDIA_FILE_MISSING"
                or not settings.crop_observation_s3_bucket
                or not s3_storage.head_object(object_key=asset["object_key"])
            ):
                raise
            return RedirectResponse(
                url=s3_storage.create_download_url(object_key=asset["object_key"]),
                status_code=307,
            )

    return RedirectResponse(
        url=s3_storage.create_download_url(object_key=asset["object_key"]),
        status_code=307,
    )
