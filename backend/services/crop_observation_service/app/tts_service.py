from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from shared.config.settings import settings
from services.crop_observation_service.app import cartesia_client
from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app.admin_schemas import (
    InstructionAudioGenerateResponse,
    TtsProfileOut,
    TtsStatusOut,
    TtsVoiceOut,
)
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.storage import active_backend, is_local


def _require_admin(context: RequestContext) -> None:
    if context.principal.role != "admin":
        raise CropObservationError("ADMIN_ONLY", "This action requires an admin account.", 403)


def get_status(context: RequestContext) -> TtsStatusOut:
    _require_admin(context)
    return TtsStatusOut(
        enabled=settings.cartesia_tts_enabled,
        provider="CARTESIA",
        model_id=settings.cartesia_tts_model,
        api_key_configured=bool(settings.cartesia_api_key),
    )


def list_profiles(context: RequestContext) -> list[TtsProfileOut]:
    _require_admin(context)
    rows = repo.list_tts_profiles()
    return [TtsProfileOut(**row) for row in rows]


def upsert_profile(
    context: RequestContext,
    *,
    locale: str,
    voice_id: str,
    voice_name: str | None,
    model_id: str | None,
    speed: float | None,
    volume: float | None,
) -> TtsProfileOut:
    _require_admin(context)
    profile_code = "odia_default" if locale == "or-IN" else "english_default"
    row = repo.upsert_tts_profile(
        profile_code=profile_code,
        locale=locale,
        provider="CARTESIA",
        model_id=model_id or settings.cartesia_tts_model,
        voice_id=voice_id,
        voice_name=voice_name,
        output_format={"container": settings.cartesia_tts_output_container},
        generation_config={
            "speed": speed if speed is not None else settings.cartesia_tts_speed,
            "volume": volume if volume is not None else settings.cartesia_tts_volume,
        },
    )
    return TtsProfileOut(**row)


def list_voices(context: RequestContext, *, language: str) -> list[TtsVoiceOut]:
    _require_admin(context)
    voices = cartesia_client.list_voices(language=language)
    result = []
    for voice in voices:
        result.append(
            TtsVoiceOut(
                voice_id=str(voice.get("id") or voice.get("voice_id")),
                name=voice.get("name") or voice.get("display_name") or "Unnamed voice",
                language=voice.get("language"),
                preview_url=voice.get("preview_file_url"),
            )
        )
    return result


def generate_instruction_audio(
    context: RequestContext,
    *,
    stage_id: UUID,
    locale: str,
    force: bool,
) -> InstructionAudioGenerateResponse:
    _require_admin(context)
    if not settings.cartesia_tts_enabled:
        raise CropObservationError("TTS_DISABLED", "Instruction audio generation is disabled.", 409)

    stage = repo.get_stage(stage_id)
    if stage is None:
        raise CropObservationError("STAGE_NOT_FOUND", "This stage was not found.", 404)

    translations = repo.get_stage_translations(stage_id)
    transcript = next(
        (
            row["instruction_text"]
            for row in translations
            if row["locale"] == locale and row["instruction_text"]
        ),
        None,
    )
    if not transcript:
        raise CropObservationError(
            "INSTRUCTION_TEXT_MISSING",
            "Add instruction text for this locale before generating audio.",
            422,
        )

    profile = repo.get_tts_profile(locale)
    if profile is None:
        raise CropObservationError("TTS_PROFILE_MISSING", "No active TTS profile exists for this locale.", 422)
    if not profile["voice_id"] or profile["voice_id"] == "__SET_IN_ENV__":
        raise CropObservationError("TTS_VOICE_ID_MISSING", "Set a voice ID for this locale before generating audio.", 422)

    generation_config = profile.get("generation_config") or {}
    output_format = profile.get("output_format") or {"container": settings.cartesia_tts_output_container}
    cache_key = sha256(
        "|".join(
            [
                str(stage_id),
                locale,
                transcript.strip(),
                profile["model_id"],
                profile["voice_id"],
                str(generation_config.get("speed", settings.cartesia_tts_speed)),
                str(generation_config.get("volume", settings.cartesia_tts_volume)),
                str(output_format.get("container", settings.cartesia_tts_output_container)),
            ]
        ).encode("utf-8")
    ).hexdigest()

    existing = repo.get_tts_generation_by_cache_key(cache_key)
    if existing and existing["status"] == "READY" and existing["system_media_asset_id"] and not force:
        return InstructionAudioGenerateResponse(
            stage_id=stage_id,
            locale=locale,
            status="READY",
            asset_id=existing["system_media_asset_id"],
            content_url=f"/v1/crop-observations/system-media/{existing['system_media_asset_id']}/content",
        )

    audio_bytes = cartesia_client.generate_audio_bytes(
        transcript=transcript,
        model_id=profile["model_id"],
        voice_id=profile["voice_id"],
        language=locale,
        speed=float(generation_config.get("speed", settings.cartesia_tts_speed)),
        volume=float(generation_config.get("volume", settings.cartesia_tts_volume)),
        container=str(output_format.get("container", settings.cartesia_tts_output_container)),
    )

    object_key = f"system/generated/stages/{stage_id}/instruction_audio/{locale}/{cache_key}.{settings.cartesia_tts_output_container}"
    active_backend().put_bytes(object_key=object_key, data=audio_bytes, mime_type="audio/mpeg")
    repo.deactivate_stage_instruction_audio(stage_id, locale)
    asset = repo.create_system_media_asset(
        asset_type="STAGE_INSTRUCTION_AUDIO",
        crop_id=None,
        stage_id=stage_id,
        bucket_name="local" if is_local() else settings.crop_observation_s3_bucket,
        object_key=object_key,
        mime_type="audio/mpeg",
        byte_size=len(audio_bytes),
        locale=locale,
        duration_seconds=None,
        storage_backend=settings.media_storage_backend.upper(),
        original_filename=f"{stage_id}-{locale}.{settings.cartesia_tts_output_container}",
    )
    repo.upsert_tts_generation(
        target_type="STAGE",
        target_id=stage_id,
        locale=locale,
        transcript=transcript,
        profile_id=profile["tts_profile_id"],
        cache_key=cache_key,
        status="READY",
        system_media_asset_id=asset["asset_id"],
        error_message=None,
    )
    return InstructionAudioGenerateResponse(
        stage_id=stage_id,
        locale=locale,
        status="READY",
        asset_id=asset["asset_id"],
        content_url=f"/v1/crop-observations/system-media/{asset['asset_id']}/content",
    )
