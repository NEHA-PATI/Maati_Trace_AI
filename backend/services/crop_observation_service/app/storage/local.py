from __future__ import annotations

from pathlib import Path

from shared.config.settings import settings
from services.crop_observation_service.app.errors import CropObservationError

# services/crop_observation_service/app/storage/local.py -> .../crop_observation_service
SERVICE_ROOT = Path(__file__).resolve().parents[2]


def _media_root() -> Path:
    root = Path(settings.local_media_root)
    root = root if root.is_absolute() else (SERVICE_ROOT / root)
    return root.resolve()


def system_media_root() -> Path:
    path = _media_root() / settings.local_system_media_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def farmer_media_root() -> Path:
    path = _media_root() / settings.local_farmer_media_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve(object_key: str) -> Path:
    """Resolve an object_key (always farmer/... or system/...) to a path
    under the local media root, refusing anything that would escape it."""
    root = _media_root()
    target = (root / object_key).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise CropObservationError(
            "INVALID_MEDIA_PATH", "Invalid media object path.", 400
        ) from exc
    return target


def create_upload_url(*, object_key: str, mime_type: str) -> dict[str, object]:
    """LOCAL equivalent of the S3 presigned-PUT contract: the browser PUTs
    the raw file straight to this same service instead of straight to S3."""
    return {
        "upload_url": f"/v1/crop-observations/media/local-content/{object_key}",
        "method": "PUT",
        "headers": {"Content-Type": mime_type},
        "expires_in_seconds": settings.s3_presigned_upload_ttl_seconds,
    }


def write_bytes(*, object_key: str, data: bytes) -> int:
    target = resolve(object_key)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    try:
        tmp.write_bytes(data)
        tmp.replace(target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return target.stat().st_size


def head_object(*, object_key: str) -> dict[str, object] | None:
    path = resolve(object_key)
    if not path.exists():
        return None
    return {"ContentLength": path.stat().st_size}


def read_bytes(*, object_key: str) -> bytes:
    path = resolve(object_key)
    if not path.exists():
        raise CropObservationError("MEDIA_FILE_MISSING", "Media file was not found on disk.", 404)
    return path.read_bytes()


def delete(*, object_key: str) -> None:
    resolve(object_key).unlink(missing_ok=True)
