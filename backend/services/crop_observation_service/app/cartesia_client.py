from __future__ import annotations

from typing import Any

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


def _request_timeout() -> tuple[float, float]:
    return (
        settings.cartesia_connect_timeout_seconds,
        settings.cartesia_read_timeout_seconds,
    )


def _voice_rows(response: requests.Response) -> list[dict[str, Any]]:
    payload = response.json()
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "voices", "items"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    return []


def list_voices(*, language: str) -> list[dict]:
    """Return voices for the admin picker.

    Cartesia has evolved its locale filtering across API versions.  The
    production service therefore first uses the language filter (``or``/``en``)
    and, if that produces no rows, tries the full locale.  This call is only an
    admin/configuration operation; it is never in the farmer hot path.
    """
    short_language = str(language).split("-", 1)[0].lower()
    attempts = [
        {"language": short_language, "expand[]": "preview_file_url"},
        {"locale": language, "expand[]": "preview_file_url"},
    ]
    last_error: Exception | None = None
    for params in attempts:
        try:
            response = requests.get(
                f"{settings.cartesia_api_base.rstrip('/')}/voices",
                headers=_headers(),
                params=params,
                timeout=_request_timeout(),
            )
            response.raise_for_status()
            rows = _voice_rows(response)
            if rows:
                return rows
        except (requests.RequestException, ValueError) as exc:
            last_error = exc

    if last_error is not None:
        raise CropObservationError(
            "TTS_PROVIDER_UNAVAILABLE",
            "Cartesia voices could not be loaded right now.",
            503,
            internal_message=str(last_error),
        ) from last_error
    return []


def generate_audio_bytes(
    *,
    transcript: str,
    model_id: str,
    voice_id: str,
    locale: str,
    speed: float,
    volume: float,
    container: str,
) -> bytes:
    """Generate one complete static instruction clip using Cartesia /tts/bytes.

    The request is pinned by the required Cartesia-Version header in settings.
    Current Cartesia bytes API uses a voice ID string and accepts either a
    language or locale value (never both). Only trusted backend/admin flows
    call this method; farmer browsers never receive the provider key.
    """
    url = f"{settings.cartesia_api_base.rstrip('/')}/tts/bytes"
    payload = {
        "model_id": model_id,
        "transcript": transcript,
        "voice": voice_id,
        "output_format": {"container": container},
        "locale": locale,
        "generation_config": {"speed": speed, "volume": volume},
    }
    try:
        response = requests.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=_request_timeout(),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        provider_response = ""
        response_obj = getattr(exc, "response", None)
        if response_obj is not None:
            try:
                provider_response = response_obj.text[:1000]
            except Exception:
                provider_response = ""
        internal = str(exc)
        if provider_response:
            internal = f"{internal}; provider_response={provider_response}"
        raise CropObservationError(
            "TTS_GENERATION_FAILED",
            "Instruction audio could not be generated right now.",
            503,
            internal_message=internal,
        ) from exc

    if not response.content:
        raise CropObservationError(
            "TTS_EMPTY_RESPONSE",
            "Cartesia returned an empty instruction audio file.",
            503,
        )
    return response.content
