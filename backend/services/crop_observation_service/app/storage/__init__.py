from __future__ import annotations

from shared.config.settings import settings
from services.crop_observation_service.app.storage import local as local_storage
from services.crop_observation_service.app.storage import s3 as s3_storage


def active_backend():
    """Return whichever storage backend module is configured. Both modules
    expose the same create_upload_url()/head_object() shape, so callers never
    need to know which one is active — see media_service.py."""
    return local_storage if settings.media_storage_backend.upper() == "LOCAL" else s3_storage


def is_local() -> bool:
    return settings.media_storage_backend.upper() == "LOCAL"
