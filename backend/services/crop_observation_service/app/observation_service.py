from __future__ import annotations

from uuid import UUID

from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app import validation_service
from services.crop_observation_service.app.clients import farm_registry as farm_registry_client
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError
from services.crop_observation_service.app.schemas import (
    DailyStatusResponse,
    DailyStatusSaveRequest,
    PracticeObservationResponse,
    PracticeSaveRequest,
)
from services.crop_observation_service.app.service import today_ist


def resolve_cycle_and_authorize(context: RequestContext, crop_cycle_id: UUID) -> dict:
    """Load the crop cycle + its farm_crop, and confirm (via
    farm_registry_service) that the calling principal may act on that farm.
    Returns the crop_cycle row."""
    cycle = repo.get_crop_cycle(crop_cycle_id)
    if cycle is None:
        raise CropObservationError("CROP_CYCLE_NOT_FOUND", "Crop cycle was not found.", 404)

    farm_crop = repo.get_farm_crop(cycle["farm_crop_id"])
    if farm_crop is None:
        raise CropObservationError("FARM_CROP_NOT_FOUND", "Farm crop was not found.", 404)

    farm_registry_client.get_authorized_farm(
        farm_crop["farm_id"],
        authorization=context.authorization,
        correlation_id=context.correlation_id,
    )
    return cycle


def save_daily_status(
    context: RequestContext,
    crop_cycle_id: UUID,
    stage_code: str,
    payload: DailyStatusSaveRequest,
) -> DailyStatusResponse:
    cycle = resolve_cycle_and_authorize(context, crop_cycle_id)

    stage = repo.get_stage_by_code(cycle["config_version_id"], stage_code)
    if stage is None:
        raise CropObservationError("CROP_STAGE_NOT_FOUND", "This crop stage was not found.", 404)

    # observed_on is always decided by the server for an online save — never
    # the client's clock, and never rewritten by a later edit on the same day.
    row = repo.upsert_daily_status(
        crop_cycle_id=crop_cycle_id,
        config_version_id=cycle["config_version_id"],
        stage_code=stage_code,
        observed_on=today_ist(),
        crop_status=payload.crop_status,
        client_entry_id=payload.client_entry_id,
        captured_at_client=payload.captured_at_client,
    )

    if payload.crop_status == "SERIOUS_PROBLEM":
        farm_crop = repo.get_farm_crop(cycle["farm_crop_id"])
        repo.create_review_flag(
            farmer_user_id=farm_crop["farmer_user_id"],
            farm_id=farm_crop["farm_id"],
            crop_cycle_id=crop_cycle_id,
            source_type="DAILY_STAGE",
            source_id=row["daily_observation_id"],
            flag_type="SERIOUS_CROP_STATUS",
            priority="HIGH",
        )

    return DailyStatusResponse(
        daily_observation_id=row["daily_observation_id"],
        crop_cycle_id=row["crop_cycle_id"],
        stage_code=row["stage_code"],
        observed_on=row["observed_on"],
        crop_status=row["crop_status"],
        client_entry_id=row["client_entry_id"],
        sync_source=row["sync_source"],
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


def save_practice_observation(
    context: RequestContext,
    crop_cycle_id: UUID,
    stage_code: str,
    practice_code: str,
    payload: PracticeSaveRequest,
) -> PracticeObservationResponse:
    cycle = resolve_cycle_and_authorize(context, crop_cycle_id)

    stage = repo.get_stage_by_code(cycle["config_version_id"], stage_code)
    if stage is None:
        raise CropObservationError("CROP_STAGE_NOT_FOUND", "This crop stage was not found.", 404)

    stage_practice = repo.get_stage_practice_by_code(stage["stage_id"], practice_code)
    if stage_practice is None:
        raise CropObservationError(
            "PRACTICE_NOT_AVAILABLE",
            "This practice is not available for this stage.",
            404,
        )

    # A practice can only be recorded against today's daily status — create
    # it (defaulting to GOOD) if the farmer hasn't logged a status yet today.
    daily = repo.get_daily_observation_by_key(crop_cycle_id, stage_code, today_ist())
    if daily is None:
        raise CropObservationError(
            "STAGE_STATUS_REQUIRED",
            "Save today's crop status before adding a practice update.",
            409,
        )

    validated_answers = validation_service.validate_practice_answers(
        stage_practice_id=stage_practice["stage_practice_id"],
        answers=payload.answers,
    )

    row = repo.upsert_practice_observation(
        daily_observation_id=daily["daily_observation_id"],
        stage_practice_id=stage_practice["stage_practice_id"],
        practice_code=practice_code,
        answers=validated_answers,
        client_entry_id=payload.client_entry_id,
    )

    return PracticeObservationResponse(
        practice_observation_id=row["practice_observation_id"],
        daily_observation_id=row["daily_observation_id"],
        practice_code=row["practice_code"],
        answers=row["answers"],
        completion_status=row["completion_status"],
        client_entry_id=row["client_entry_id"],
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )
