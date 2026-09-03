from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import Response

from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.storage import is_local
from services.crop_observation_service.app.storage import local as local_storage

router = APIRouter(prefix="/v1/crop-observations/system-media", tags=["system-media"])


@router.get("/{asset_id}/content")
def get_system_media_content_endpoint(asset_id: UUID):
    """Crop card images, stage images and instruction audio are admin-curated
    reference content (not farmer data), so — same as GET /crops — this is
    intentionally unauthenticated, matching the rest of the read-only crop
    catalogue."""
    asset = repo.get_system_media_asset(asset_id)
    if asset is None:
        raise CropObservationError("MEDIA_NOT_FOUND", "Media asset was not found.", 404)
    if not is_local():
        raise CropObservationError(
            "MEDIA_CONTENT_NOT_LOCAL",
            "This media is stored remotely — use its presigned URL instead.",
            409,
        )
    data = local_storage.read_bytes(object_key=asset["object_key"])
    return Response(content=data, media_type=asset["mime_type"])
