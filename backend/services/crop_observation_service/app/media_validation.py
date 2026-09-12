from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from services.crop_observation_service.app.errors import CropObservationError


_IMAGE_FORMATS = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def validate_image_bytes(data: bytes, mime_type: str) -> None:
    expected_format = _IMAGE_FORMATS.get(mime_type.lower())
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
        actual_format = image.format
    except (UnidentifiedImageError, OSError) as exc:
        raise CropObservationError("INVALID_MEDIA_FILE", "This does not look like a valid image.", 422) from exc
    if expected_format and actual_format != expected_format:
        raise CropObservationError("MEDIA_TYPE_MISMATCH", "The file contents do not match the declared image type.", 422)


def validate_audio_bytes(data: bytes, mime_type: str) -> None:
    """Validate container/frame magic before an asset becomes READY."""
    mime = mime_type.lower().split(";", 1)[0].strip()
    valid = False
    if mime in {"audio/wav", "audio/x-wav"}:
        valid = len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    elif mime == "audio/ogg":
        valid = data.startswith(b"OggS")
    elif mime == "audio/webm":
        valid = data.startswith(b"\x1a\x45\xdf\xa3")
    elif mime == "audio/mp4":
        valid = len(data) >= 12 and data[4:8] == b"ftyp"
    elif mime == "audio/mpeg":
        valid = data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0)
    if not valid:
        raise CropObservationError("INVALID_MEDIA_FILE", "The uploaded audio file is not a valid audio container.", 422)
