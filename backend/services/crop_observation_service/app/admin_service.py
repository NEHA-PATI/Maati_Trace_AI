from __future__ import annotations

from typing import Any
from uuid import UUID

from services.crop_observation_service.app import admin_repository as admin_repo
from services.crop_observation_service.app import repository as repo
from services.crop_observation_service.app import tts_service
from services.crop_observation_service.app.admin_repository import VALID_FIELD_TYPES
from services.crop_observation_service.app.admin_schemas import (
    AdminConfigVersionOut,
    AdminCropCreateRequest,
    AdminCropOut,
    AdminCropUpdateRequest,
    AdminFieldCreateRequest,
    AdminFieldOut,
    AdminFieldUpdateRequest,
    AdminOptionCreateRequest,
    AdminOptionOut,
    AdminOptionUpdateRequest,
    AdminPracticeTemplateOut,
    AdminStageCreateRequest,
    AdminStageOut,
    AdminStagePracticeCreateRequest,
    AdminStagePracticeOut,
    AdminStagePracticeUpdateRequest,
    AdminStageUpdateRequest,
    CropTranslationUpsertRequest,
    FieldTranslationUpsertRequest,
    ObservationDetailOut,
    ObservationListItemOut,
    ObservationSummaryOut,
    OptionTranslationUpsertRequest,
    PracticeTranslationUpsertRequest,
    StageTranslationUpsertRequest,
    TtsProfileUpsertRequest,
    TtsProfileOut,
    TtsStatusOut,
    TtsVoiceOut,
    ValidationIssue,
    ValidationResponse,
)
from services.crop_observation_service.app.dependencies import RequestContext
from services.crop_observation_service.app.errors import CropObservationError

REQUIRED_LOCALES = ("en-IN", "or-IN")
CHOICE_FIELD_TYPES = {"SINGLE_CHOICE", "MULTI_CHOICE", "PICTURE_CHOICE", "PRODUCT", "PEST", "DISEASE"}
MAX_COMFORTABLE_REQUIRED_FIELDS = 6


def require_admin(context: RequestContext) -> None:
    if context.principal.role != "admin":
        raise CropObservationError("ADMIN_ONLY", "This action requires an admin account.", 403)


# ---------------------------------------------------------------------------
# Crops
# ---------------------------------------------------------------------------


def list_crops(context: RequestContext) -> list[AdminCropOut]:
    require_admin(context)
    return [AdminCropOut(**row) for row in admin_repo.list_all_crops()]


def create_crop(context: RequestContext, payload: AdminCropCreateRequest) -> AdminCropOut:
    require_admin(context)
    if repo.get_crop_by_code(payload.crop_code) is not None:
        raise CropObservationError("CROP_ALREADY_EXISTS", "This crop code is already in use.", 409)
    row = admin_repo.create_crop(
        crop_code=payload.crop_code,
        lifecycle_type=payload.lifecycle_type,
        default_stage_strategy=payload.default_stage_strategy,
        display_order=payload.display_order,
    )
    return AdminCropOut(**row)


def get_crop(context: RequestContext, crop_code: str) -> AdminCropOut:
    require_admin(context)
    crop = admin_repo.get_crop(crop_code)
    if crop is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop was not found.", 404)
    return AdminCropOut(**crop)


def update_crop(context: RequestContext, crop_code: str, payload: AdminCropUpdateRequest) -> AdminCropOut:
    require_admin(context)
    if repo.get_crop_by_code(crop_code) is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop was not found.", 404)
    fields = payload.model_dump(exclude_unset=True)
    row = admin_repo.update_crop(crop_code, fields)
    return AdminCropOut(**row)


def upsert_crop_translation(
    context: RequestContext, crop_code: str, locale: str, payload: CropTranslationUpsertRequest
) -> dict[str, str]:
    require_admin(context)
    crop = repo.get_crop_by_code(crop_code)
    if crop is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop was not found.", 404)
    admin_repo.upsert_crop_translation(crop["crop_id"], locale, payload.display_name, payload.short_description)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Configuration versions
# ---------------------------------------------------------------------------


def list_configurations(context: RequestContext, crop_code: str) -> list[AdminConfigVersionOut]:
    require_admin(context)
    crop = repo.get_crop_by_code(crop_code)
    if crop is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop was not found.", 404)
    return [AdminConfigVersionOut(**row) for row in admin_repo.list_configurations(crop["crop_id"])]


def create_draft_configuration(context: RequestContext, crop_code: str) -> AdminConfigVersionOut:
    require_admin(context)
    crop = repo.get_crop_by_code(crop_code)
    if crop is None:
        raise CropObservationError("CROP_NOT_FOUND", "This crop was not found.", 404)
    version_number = admin_repo.next_version_number(crop["crop_id"])
    row = admin_repo.create_draft_configuration(
        crop_id=crop["crop_id"], version_number=version_number, created_by_user_id=context.principal.user_id
    )
    return AdminConfigVersionOut(**row)


def clone_configuration(context: RequestContext, config_version_id: UUID) -> AdminConfigVersionOut:
    require_admin(context)
    source = admin_repo.get_configuration(config_version_id)
    if source is None:
        raise CropObservationError("CONFIGURATION_NOT_FOUND", "This configuration was not found.", 404)

    version_number = admin_repo.next_version_number(source["crop_id"])
    draft = admin_repo.clone_configuration(
        source_config_version_id=config_version_id,
        crop_id=source["crop_id"],
        version_number=version_number,
        created_by_user_id=context.principal.user_id,
    )
    return AdminConfigVersionOut(**draft)


def validate_configuration(context: RequestContext, config_version_id: UUID) -> ValidationResponse:
    require_admin(context)
    config = admin_repo.get_configuration(config_version_id)
    if config is None:
        raise CropObservationError("CONFIGURATION_NOT_FOUND", "This configuration was not found.", 404)

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    crop_locales = set(admin_repo.count_locales_for_crop(config["crop_id"]))
    for locale in REQUIRED_LOCALES:
        if locale not in crop_locales:
            errors.append(ValidationIssue(code="CROP_TRANSLATION_MISSING", locale=locale))

    stages = admin_repo.list_stages_for_config(config_version_id)
    if not stages:
        errors.append(ValidationIssue(code="NO_STAGES"))
    if stages and not any(s["is_initial"] for s in stages):
        errors.append(ValidationIssue(code="NO_INITIAL_STAGE"))

    for stage in stages:
        translations = {row["locale"]: row for row in repo.get_stage_translations(stage["stage_id"])}
        for locale in REQUIRED_LOCALES:
            translation = translations.get(locale)
            if translation is None:
                errors.append(ValidationIssue(code="STAGE_TRANSLATION_MISSING", stage_code=stage["stage_code"], locale=locale))
                continue
            if not str(translation.get("instruction_text") or "").strip():
                errors.append(ValidationIssue(code="STAGE_INSTRUCTION_TEXT_MISSING", stage_code=stage["stage_code"], locale=locale))

        if repo.get_stage_image(stage["stage_id"]) is None:
            errors.append(ValidationIssue(code="STAGE_IMAGE_MISSING", stage_code=stage["stage_code"]))

        for locale in REQUIRED_LOCALES:
            if repo.get_stage_instruction_audio(stage["stage_id"], locale=locale) is None:
                errors.append(ValidationIssue(code="STAGE_INSTRUCTION_AUDIO_MISSING", stage_code=stage["stage_code"], locale=locale))

        stage_practices = admin_repo.list_stage_practices_for_stage(stage["stage_id"])
        for sp in stage_practices:
            practice_locales = {item["locale"] for item in repo.get_practice_translations(sp["practice_template_id"])}
            for locale in REQUIRED_LOCALES:
                if locale not in practice_locales:
                    errors.append(ValidationIssue(code="PRACTICE_TRANSLATION_MISSING", stage_code=stage["stage_code"], practice_code=sp["practice_code"], locale=locale))
            fields = admin_repo.list_fields_for_stage_practice(sp["stage_practice_id"])
            required_field_count = sum(1 for f in fields if f["is_required"])
            if required_field_count > MAX_COMFORTABLE_REQUIRED_FIELDS:
                warnings.append(ValidationIssue(code="FORM_TOO_LONG", stage_code=stage["stage_code"], practice_code=sp["practice_code"]))

            media_config = sp.get("media_config") or {}
            for section in ("issue_evidence", "practice_evidence"):
                rule = media_config.get(section) or {}
                if rule.get("enabled"):
                    max_images = int(rule.get("max_images") or 0)
                    if max_images < 1 or max_images > 2:
                        errors.append(ValidationIssue(code="MEDIA_IMAGE_LIMIT_INVALID", stage_code=stage["stage_code"], practice_code=sp["practice_code"]))
            voice = media_config.get("voice_note") or {}
            if voice.get("enabled"):
                max_seconds = int(voice.get("max_seconds") or 0)
                if max_seconds < 5 or max_seconds > 60:
                    errors.append(ValidationIssue(code="MEDIA_VOICE_LIMIT_INVALID", stage_code=stage["stage_code"], practice_code=sp["practice_code"]))

            for field in fields:
                field_locales = set(admin_repo.count_locales_for_field(field["field_definition_id"]))
                for locale in REQUIRED_LOCALES:
                    if locale not in field_locales:
                        errors.append(ValidationIssue(code="FIELD_TRANSLATION_MISSING", stage_code=stage["stage_code"], practice_code=sp["practice_code"], field_code=field["field_code"], locale=locale))

                if field["field_type"] in CHOICE_FIELD_TYPES:
                    options = admin_repo.list_options_for_field(field["field_definition_id"])
                    if not options:
                        errors.append(ValidationIssue(code="FIELD_OPTIONS_MISSING", stage_code=stage["stage_code"], practice_code=sp["practice_code"], field_code=field["field_code"]))
                    for option in options:
                        option_locales = set(admin_repo.count_locales_for_option(option["field_option_id"]))
                        for locale in REQUIRED_LOCALES:
                            if locale not in option_locales:
                                errors.append(ValidationIssue(code="OPTION_TRANSLATION_MISSING", stage_code=stage["stage_code"], practice_code=sp["practice_code"], field_code=field["field_code"], locale=locale))
                        if field["field_type"] == "PICTURE_CHOICE":
                            if not repo.list_system_media_bindings(target_type="FIELD_OPTION", target_id=option["field_option_id"], asset_role="OPTION_IMAGE", limit=1):
                                warnings.append(ValidationIssue(code="OPTION_IMAGE_MISSING", stage_code=stage["stage_code"], practice_code=sp["practice_code"], field_code=field["field_code"]))

    return ValidationResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)


def publish_configuration(context: RequestContext, config_version_id: UUID) -> AdminConfigVersionOut:
    require_admin(context)
    config = admin_repo.get_configuration(config_version_id)
    if config is None:
        raise CropObservationError("CONFIGURATION_NOT_FOUND", "This configuration was not found.", 404)
    if config["status"] != "DRAFT":
        raise CropObservationError(
            "CONFIGURATION_NOT_DRAFT", "Only a draft configuration can be published.", 409
        )

    validation = validate_configuration(context, config_version_id)
    if not validation.valid:
        raise CropObservationError(
            "CONFIGURATION_INVALID",
            "This configuration has validation errors and cannot be published.",
            422,
            fields=[issue.model_dump() for issue in validation.errors],
        )

    # Existing active crop cycles keep pointing at their own config_version_id
    # (see crop_cycles.config_version_id) — publishing never touches them.
    admin_repo.supersede_published_configuration(config["crop_id"])
    row = admin_repo.publish_configuration(config_version_id, published_by_user_id=context.principal.user_id)
    return AdminConfigVersionOut(**row)


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


def create_stage(
    context: RequestContext, config_version_id: UUID, payload: AdminStageCreateRequest
) -> AdminStageOut:
    require_admin(context)
    _require_draft(config_version_id)
    row = admin_repo.create_stage(
        config_version_id=config_version_id,
        stage_code=payload.stage_code,
        display_order=payload.display_order,
        is_initial=payload.is_initial,
    )
    return AdminStageOut(**row)


def update_stage(context: RequestContext, stage_id: UUID, payload: AdminStageUpdateRequest) -> AdminStageOut:
    require_admin(context)
    stage = admin_repo.get_stage(stage_id)
    if stage is None:
        raise CropObservationError("STAGE_NOT_FOUND", "This stage was not found.", 404)
    _require_draft(stage["config_version_id"])
    fields = payload.model_dump(exclude_unset=True)
    row = admin_repo.update_stage(stage_id, fields)
    return AdminStageOut(**row)


def delete_stage(context: RequestContext, stage_id: UUID) -> None:
    require_admin(context)
    stage = admin_repo.get_stage(stage_id)
    if stage is None:
        raise CropObservationError("STAGE_NOT_FOUND", "This stage was not found.", 404)
    _require_draft(stage["config_version_id"])
    admin_repo.delete_stage(stage_id)


def reorder_stages(context: RequestContext, config_version_id: UUID, order: list[UUID]) -> None:
    require_admin(context)
    _require_draft(config_version_id)
    admin_repo.reorder_stages(order)


def upsert_stage_translation(
    context: RequestContext, stage_id: UUID, locale: str, payload: StageTranslationUpsertRequest
) -> dict[str, str]:
    require_admin(context)
    stage = admin_repo.get_stage(stage_id)
    if stage is None:
        raise CropObservationError("STAGE_NOT_FOUND", "This stage was not found.", 404)
    _require_draft(stage["config_version_id"])
    before = next((row for row in repo.get_stage_translations(stage_id) if row["locale"] == locale), None)
    values = payload.model_dump()
    admin_repo.upsert_stage_translation(stage_id, locale, values)

    # Instruction audio is derived content. If the approved text changes, the
    # previous clip is no longer a valid binding for this draft stage. The
    # immutable physical file remains reusable by other versions/stages.
    if before is not None and (before.get("instruction_text") or "") != (values.get("instruction_text") or ""):
        repo.deactivate_system_media_for_target(
            target_type="STAGE",
            target_id=stage_id,
            asset_role="INSTRUCTION_AUDIO",
            locale=locale,
        )
    return {"status": "ok"}


def _require_draft(config_version_id: UUID) -> dict[str, Any]:
    config = admin_repo.get_configuration(config_version_id)
    if config is None:
        raise CropObservationError("CONFIGURATION_NOT_FOUND", "This configuration was not found.", 404)
    if config["status"] != "DRAFT":
        raise CropObservationError(
            "CONFIGURATION_NOT_DRAFT", "Only a draft configuration can be edited.", 409
        )
    return config


# ---------------------------------------------------------------------------
# Stage practices
# ---------------------------------------------------------------------------


def list_practice_templates(context: RequestContext) -> list[AdminPracticeTemplateOut]:
    require_admin(context)
    return [AdminPracticeTemplateOut(**row) for row in admin_repo.list_practice_templates()]


def create_stage_practice(
    context: RequestContext, stage_id: UUID, payload: AdminStagePracticeCreateRequest
) -> AdminStagePracticeOut:
    require_admin(context)
    stage = admin_repo.get_stage(stage_id)
    if stage is None:
        raise CropObservationError("STAGE_NOT_FOUND", "This stage was not found.", 404)
    _require_draft(stage["config_version_id"])

    template = admin_repo.get_practice_template_by_code(payload.practice_code)
    if template is None:
        raise CropObservationError("PRACTICE_TEMPLATE_NOT_FOUND", "This practice code is not recognised.", 404)

    row = admin_repo.create_stage_practice(
        stage_id=stage_id,
        practice_template_id=template["practice_template_id"],
        availability_scope=payload.availability_scope,
        display_order=payload.display_order,
        media_config=payload.media_config,
    )
    return AdminStagePracticeOut(**row)


def update_stage_practice(
    context: RequestContext, stage_practice_id: UUID, payload: AdminStagePracticeUpdateRequest
) -> AdminStagePracticeOut:
    require_admin(context)
    sp = admin_repo.get_stage_practice(stage_practice_id)
    if sp is None:
        raise CropObservationError("STAGE_PRACTICE_NOT_FOUND", "This stage practice was not found.", 404)
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    fields = payload.model_dump(exclude_unset=True)
    row = admin_repo.update_stage_practice(stage_practice_id, fields)
    return AdminStagePracticeOut(**row)


def delete_stage_practice(context: RequestContext, stage_practice_id: UUID) -> None:
    require_admin(context)
    sp = admin_repo.get_stage_practice(stage_practice_id)
    if sp is None:
        raise CropObservationError("STAGE_PRACTICE_NOT_FOUND", "This stage practice was not found.", 404)
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    admin_repo.delete_stage_practice(stage_practice_id)


def upsert_practice_translation(
    context: RequestContext, practice_template_id: UUID, locale: str, payload: PracticeTranslationUpsertRequest
) -> dict[str, str]:
    require_admin(context)
    admin_repo.upsert_practice_translation(practice_template_id, locale, payload.model_dump())
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------


def create_field(
    context: RequestContext, stage_practice_id: UUID, payload: AdminFieldCreateRequest
) -> AdminFieldOut:
    require_admin(context)
    sp = admin_repo.get_stage_practice(stage_practice_id)
    if sp is None:
        raise CropObservationError("STAGE_PRACTICE_NOT_FOUND", "This stage practice was not found.", 404)
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])

    if payload.field_type not in VALID_FIELD_TYPES:
        raise CropObservationError("INVALID_FIELD_TYPE", "Unsupported field type.", 422)

    row = admin_repo.create_field(
        stage_practice_id=stage_practice_id,
        field_code=payload.field_code,
        field_type=payload.field_type,
        semantic_type=payload.semantic_type,
        display_order=payload.display_order,
        is_required=payload.is_required,
    )
    return AdminFieldOut(**row)


def update_field(context: RequestContext, field_definition_id: UUID, payload: AdminFieldUpdateRequest) -> AdminFieldOut:
    require_admin(context)
    field = admin_repo.get_field(field_definition_id)
    if field is None:
        raise CropObservationError("FIELD_NOT_FOUND", "This field was not found.", 404)
    sp = admin_repo.get_stage_practice(field["stage_practice_id"])
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    fields = payload.model_dump(exclude_unset=True)
    row = admin_repo.update_field(field_definition_id, fields)
    return AdminFieldOut(**row)


def delete_field(context: RequestContext, field_definition_id: UUID) -> None:
    require_admin(context)
    field = admin_repo.get_field(field_definition_id)
    if field is None:
        raise CropObservationError("FIELD_NOT_FOUND", "This field was not found.", 404)
    sp = admin_repo.get_stage_practice(field["stage_practice_id"])
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    admin_repo.delete_field(field_definition_id)


def reorder_fields(context: RequestContext, stage_practice_id: UUID, order: list[UUID]) -> None:
    require_admin(context)
    sp = admin_repo.get_stage_practice(stage_practice_id)
    if sp is None:
        raise CropObservationError("STAGE_PRACTICE_NOT_FOUND", "This stage practice was not found.", 404)
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    admin_repo.reorder_fields(stage_practice_id, order)


def upsert_field_translation(
    context: RequestContext, field_definition_id: UUID, locale: str, payload: FieldTranslationUpsertRequest
) -> dict[str, str]:
    require_admin(context)
    field = admin_repo.get_field(field_definition_id)
    if field is None:
        raise CropObservationError("FIELD_NOT_FOUND", "This field was not found.", 404)
    admin_repo.upsert_field_translation(field_definition_id, locale, payload.model_dump())
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


def create_option(context: RequestContext, field_definition_id: UUID, payload: AdminOptionCreateRequest) -> AdminOptionOut:
    require_admin(context)
    field = admin_repo.get_field(field_definition_id)
    if field is None:
        raise CropObservationError("FIELD_NOT_FOUND", "This field was not found.", 404)
    sp = admin_repo.get_stage_practice(field["stage_practice_id"])
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    row = admin_repo.create_option(
        field_definition_id=field_definition_id,
        option_code=payload.option_code,
        display_order=payload.display_order,
    )
    return AdminOptionOut(**row)


def update_option(context: RequestContext, field_option_id: UUID, payload: AdminOptionUpdateRequest) -> AdminOptionOut:
    require_admin(context)
    option = admin_repo.get_option(field_option_id)
    if option is None:
        raise CropObservationError("OPTION_NOT_FOUND", "This option was not found.", 404)
    field = admin_repo.get_field(option["field_definition_id"])
    sp = admin_repo.get_stage_practice(field["stage_practice_id"])
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    fields = payload.model_dump(exclude_unset=True)
    row = admin_repo.update_option(field_option_id, fields)
    return AdminOptionOut(**row)


def delete_option(context: RequestContext, field_option_id: UUID) -> None:
    require_admin(context)
    option = admin_repo.get_option(field_option_id)
    if option is None:
        raise CropObservationError("OPTION_NOT_FOUND", "This option was not found.", 404)
    field = admin_repo.get_field(option["field_definition_id"])
    sp = admin_repo.get_stage_practice(field["stage_practice_id"])
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    admin_repo.delete_option(field_option_id)


def upsert_option_translation(
    context: RequestContext, field_option_id: UUID, locale: str, payload: OptionTranslationUpsertRequest
) -> dict[str, str]:
    require_admin(context)
    option = admin_repo.get_option(field_option_id)
    if option is None:
        raise CropObservationError("OPTION_NOT_FOUND", "This option was not found.", 404)
    field = admin_repo.get_field(option["field_definition_id"])
    sp = admin_repo.get_stage_practice(field["stage_practice_id"])
    stage = admin_repo.get_stage(sp["stage_id"])
    _require_draft(stage["config_version_id"])
    admin_repo.upsert_option_translation(field_option_id, locale, payload.label)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Observation monitor
# ---------------------------------------------------------------------------


def get_observations_summary(context: RequestContext) -> ObservationSummaryOut:
    require_admin(context)
    return ObservationSummaryOut(**admin_repo.observations_summary())


def list_observations(
    context: RequestContext,
    *,
    crop_code: str | None,
    status: str | None,
    from_date,
    to_date,
    limit: int,
    offset: int,
) -> list[ObservationListItemOut]:
    require_admin(context)
    rows = admin_repo.list_observations(
        crop_code=crop_code, status=status, from_date=from_date, to_date=to_date, limit=limit, offset=offset
    )
    return [ObservationListItemOut(**row) for row in rows]


def get_observation_detail(context: RequestContext, daily_observation_id: UUID) -> ObservationDetailOut:
    require_admin(context)
    row = admin_repo.get_observation_detail(daily_observation_id)
    if row is None:
        raise CropObservationError("OBSERVATION_NOT_FOUND", "Observation was not found.", 404)
    practices = repo.list_practice_observations_for_daily(daily_observation_id)
    return ObservationDetailOut(
        **row,
        practices=[{"practice_code": p["practice_code"], "answers": p["answers"]} for p in practices],
    )


def get_tts_status(context: RequestContext) -> TtsStatusOut:
    return tts_service.get_status(context)


def list_tts_profiles(context: RequestContext) -> list[TtsProfileOut]:
    return tts_service.list_profiles(context)


def upsert_tts_profile(context: RequestContext, locale: str, payload: TtsProfileUpsertRequest) -> TtsProfileOut:
    return tts_service.upsert_profile(
        context,
        locale=locale,
        voice_id=payload.voice_id,
        voice_name=payload.voice_name,
        model_id=payload.model_id,
        speed=payload.speed,
        volume=payload.volume,
    )


def list_tts_voices(context: RequestContext, language: str) -> list[TtsVoiceOut]:
    return tts_service.list_voices(context, language=language)


def generate_stage_instruction_audio(context: RequestContext, stage_id: UUID, locale: str, force: bool):
    return tts_service.generate_instruction_audio(context, stage_id=stage_id, locale=locale, force=force)
