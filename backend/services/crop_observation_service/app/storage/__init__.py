from shared.config.settings import settings
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.storage import local as local_storage
from services.crop_observation_service.app.storage import s3 as s3_storage

_ALLOWED_BACKENDS = {"LOCAL", "S3"}


def _normalize_backend(value: str | None) -> str:
    backend = (value or settings.media_storage_backend or "LOCAL").upper().strip()
    if backend not in _ALLOWED_BACKENDS:
        raise CropObservationError(
            "INVALID_STORAGE_BACKEND",
            f"Unsupported media storage backend: {backend}",
            500,
        )
    return backend


def active_backend():
    backend = _normalize_backend(settings.media_storage_backend)
    return local_storage if backend == "LOCAL" else s3_storage


def backend_for(storage_backend: str | None):
    """Resolve the backend recorded on an asset row.

    This lets a deployment switch MEDIA_STORAGE_BACKEND from LOCAL to S3
    without making legacy LOCAL rows unreadable. New writes use active_backend;
    reads/finalization use the backend recorded on the row.
    """
    backend = _normalize_backend(storage_backend)
    return local_storage if backend == "LOCAL" else s3_storage


def is_local() -> bool:
    return _normalize_backend(settings.media_storage_backend) == "LOCAL"
