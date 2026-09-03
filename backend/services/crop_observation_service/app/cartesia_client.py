from __future__ import annotations

import requests

from shared.config.settings import settings
from services.crop_observation_service.app.errors import CropObservationError


def _headers() -> dict[str, str]:
    if not settings.cartesia_api_key:
        raise CropObservationError(
            "TTS_NOT_CONFIGURED",
            "Cartesia is not configured on this environment yet.",
            503,
        )
    return {
        "Authorization": f"Bearer {settings.cartesia_api_key}",
        "Cartesia-Version": settings.cartesia_api_version,
    }


def list_voices(*, language: str) -> list[dict]:
    try:
        response = requests.get(
            f"{settings.cartesia_api_base}/voices",
            headers=_headers(),
            params={"language": language, "expand[]": "preview_file_url"},
            timeout=(settings.cartesia_connect_timeout_seconds, settings.cartesia_read_timeout_seconds),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CropObservationError(
            "TTS_PROVIDER_UNAVAILABLE",
            "Cartesia could not be reached right now.",
            503,
            internal_message=str(exc),
        ) from exc
    payload = response.json()
    return payload if isinstance(payload, list) else payload.get("data", [])


def generate_audio_bytes(
    *,
    transcript: str,
    model_id: str,
    voice_id: str,
    language: str,
    speed: float,
    volume: float,
    container: str,
) -> bytes:
    try:
        response = requests.post(
            f"{settings.cartesia_api_base}/tts/bytes",
            headers={
                **_headers(),
                "Content-Type": "application/json",
            },
            json={
                "model_id": model_id,
                "transcript": transcript,
                "voice": {"mode": "id", "id": voice_id},
                "language": language.split("-", 1)[0].lower(),
                "output_format": {"container": container},
                "generation_config": {"speed": speed, "volume": volume},
            },
            timeout=(settings.cartesia_connect_timeout_seconds, settings.cartesia_read_timeout_seconds),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CropObservationError(
            "TTS_GENERATION_FAILED",
            "Instruction audio could not be generated right now.",
            503,
            internal_message=str(exc),
        ) from exc
    return response.content
