from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from services.crop_observation_service.app import admin_repository as admin_repo
from services.crop_observation_service.app import admin_service
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
    ReorderRequest,
    StageTranslationUpsertRequest,
    ValidationResponse,
)
from services.crop_observation_service.app.dependencies import RequestContext, get_request_context

router = APIRouter(prefix="/v1/crop-observations/admin", tags=["admin"])

# --- Crops -------------------------------------------------------------


@router.get("/crops", response_model=list[AdminCropOut])
def list_crops_endpoint(context: RequestContext = Depends(get_request_context)):
    return admin_service.list_crops(context)


@router.post("/crops", response_model=AdminCropOut, status_code=201)
def create_crop_endpoint(payload: AdminCropCreateRequest, context: RequestContext = Depends(get_request_context)):
    return admin_service.create_crop(context, payload)


@router.get("/crops/{crop_code}", response_model=AdminCropOut)
def get_crop_endpoint(crop_code: str, context: RequestContext = Depends(get_request_context)):
    return admin_service.get_crop(context, crop_code)


@router.patch("/crops/{crop_code}", response_model=AdminCropOut)
def update_crop_endpoint(
    crop_code: str, payload: AdminCropUpdateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.update_crop(context, crop_code, payload)


# --- Configurations ------------------------------------------------------


@router.get("/crops/{crop_code}/configurations", response_model=list[AdminConfigVersionOut])
def list_configurations_endpoint(crop_code: str, context: RequestContext = Depends(get_request_context)):
    return admin_service.list_configurations(context, crop_code)


@router.post("/crops/{crop_code}/configurations/draft", response_model=AdminConfigVersionOut, status_code=201)
def create_draft_configuration_endpoint(crop_code: str, context: RequestContext = Depends(get_request_context)):
    return admin_service.create_draft_configuration(context, crop_code)


@router.post("/configurations/{config_version_id}/clone", response_model=AdminConfigVersionOut, status_code=201)
def clone_configuration_endpoint(
    config_version_id: UUID, context: RequestContext = Depends(get_request_context)
):
    return admin_service.clone_configuration(context, config_version_id)


@router.post("/configurations/{config_version_id}/validate", response_model=ValidationResponse)
def validate_configuration_endpoint(
    config_version_id: UUID, context: RequestContext = Depends(get_request_context)
):
    return admin_service.validate_configuration(context, config_version_id)


@router.post("/configurations/{config_version_id}/publish", response_model=AdminConfigVersionOut)
def publish_configuration_endpoint(
    config_version_id: UUID, context: RequestContext = Depends(get_request_context)
):
    return admin_service.publish_configuration(context, config_version_id)


@router.get("/configurations/{config_version_id}/stages", response_model=list[AdminStageOut])
def list_stages_endpoint(config_version_id: UUID, context: RequestContext = Depends(get_request_context)):

    admin_service.require_admin(context)
    return admin_repo.list_stages_for_config(config_version_id)


# --- Stages ----------------------------------------------------------------


@router.post("/configurations/{config_version_id}/stages", response_model=AdminStageOut, status_code=201)
def create_stage_endpoint(
    config_version_id: UUID, payload: AdminStageCreateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.create_stage(context, config_version_id, payload)


@router.patch("/stages/{stage_id}", response_model=AdminStageOut)
def update_stage_endpoint(
    stage_id: UUID, payload: AdminStageUpdateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.update_stage(context, stage_id, payload)


@router.delete("/stages/{stage_id}", status_code=204)
def delete_stage_endpoint(stage_id: UUID, context: RequestContext = Depends(get_request_context)):
    admin_service.delete_stage(context, stage_id)


@router.put("/configurations/{config_version_id}/stage-order", status_code=204)
def reorder_stages_endpoint(
    config_version_id: UUID, payload: ReorderRequest, context: RequestContext = Depends(get_request_context)
):
    admin_service.reorder_stages(context, config_version_id, payload.order)


@router.put("/stages/{stage_id}/translations/{locale}")
def upsert_stage_translation_endpoint(
    stage_id: UUID,
    locale: str,
    payload: StageTranslationUpsertRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.upsert_stage_translation(context, stage_id, locale, payload)


# --- Practices ---------------------------------------------------------


@router.get("/practice-templates", response_model=list[AdminPracticeTemplateOut])
def list_practice_templates_endpoint(context: RequestContext = Depends(get_request_context)):
    return admin_service.list_practice_templates(context)


@router.post("/stages/{stage_id}/practices", response_model=AdminStagePracticeOut, status_code=201)
def create_stage_practice_endpoint(
    stage_id: UUID,
    payload: AdminStagePracticeCreateRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.create_stage_practice(context, stage_id, payload)


@router.get("/stages/{stage_id}/practices", response_model=list[AdminStagePracticeOut])
def list_stage_practices_endpoint(stage_id: UUID, context: RequestContext = Depends(get_request_context)):

    admin_service.require_admin(context)
    return admin_repo.list_stage_practices_for_stage(stage_id)


@router.patch("/stage-practices/{stage_practice_id}", response_model=AdminStagePracticeOut)
def update_stage_practice_endpoint(
    stage_practice_id: UUID,
    payload: AdminStagePracticeUpdateRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.update_stage_practice(context, stage_practice_id, payload)


@router.delete("/stage-practices/{stage_practice_id}", status_code=204)
def delete_stage_practice_endpoint(
    stage_practice_id: UUID, context: RequestContext = Depends(get_request_context)
):
    admin_service.delete_stage_practice(context, stage_practice_id)


@router.put("/practices/{practice_template_id}/translations/{locale}")
def upsert_practice_translation_endpoint(
    practice_template_id: UUID,
    locale: str,
    payload: PracticeTranslationUpsertRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.upsert_practice_translation(context, practice_template_id, locale, payload)


# --- Fields --------------------------------------------------------------


@router.post("/stage-practices/{stage_practice_id}/fields", response_model=AdminFieldOut, status_code=201)
def create_field_endpoint(
    stage_practice_id: UUID, payload: AdminFieldCreateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.create_field(context, stage_practice_id, payload)


@router.get("/stage-practices/{stage_practice_id}/fields", response_model=list[AdminFieldOut])
def list_fields_endpoint(stage_practice_id: UUID, context: RequestContext = Depends(get_request_context)):

    admin_service.require_admin(context)
    return admin_repo.list_fields_for_stage_practice(stage_practice_id)


@router.patch("/fields/{field_id}", response_model=AdminFieldOut)
def update_field_endpoint(
    field_id: UUID, payload: AdminFieldUpdateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.update_field(context, field_id, payload)


@router.delete("/fields/{field_id}", status_code=204)
def delete_field_endpoint(field_id: UUID, context: RequestContext = Depends(get_request_context)):
    admin_service.delete_field(context, field_id)


@router.put("/stage-practices/{stage_practice_id}/field-order", status_code=204)
def reorder_fields_endpoint(
    stage_practice_id: UUID, payload: ReorderRequest, context: RequestContext = Depends(get_request_context)
):
    admin_service.reorder_fields(context, stage_practice_id, payload.order)


@router.put("/fields/{field_id}/translations/{locale}")
def upsert_field_translation_endpoint(
    field_id: UUID,
    locale: str,
    payload: FieldTranslationUpsertRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.upsert_field_translation(context, field_id, locale, payload)


# --- Options ---------------------------------------------------------------


@router.post("/fields/{field_id}/options", response_model=AdminOptionOut, status_code=201)
def create_option_endpoint(
    field_id: UUID, payload: AdminOptionCreateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.create_option(context, field_id, payload)


@router.get("/fields/{field_id}/options", response_model=list[AdminOptionOut])
def list_options_endpoint(field_id: UUID, context: RequestContext = Depends(get_request_context)):

    admin_service.require_admin(context)
    return admin_repo.list_options_for_field(field_id)


@router.patch("/options/{option_id}", response_model=AdminOptionOut)
def update_option_endpoint(
    option_id: UUID, payload: AdminOptionUpdateRequest, context: RequestContext = Depends(get_request_context)
):
    return admin_service.update_option(context, option_id, payload)


@router.delete("/options/{option_id}", status_code=204)
def delete_option_endpoint(option_id: UUID, context: RequestContext = Depends(get_request_context)):
    admin_service.delete_option(context, option_id)


@router.put("/options/{option_id}/translations/{locale}")
def upsert_option_translation_endpoint(
    option_id: UUID,
    locale: str,
    payload: OptionTranslationUpsertRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.upsert_option_translation(context, option_id, locale, payload)


# --- Crop translations -----------------------------------------------------


@router.put("/crops/{crop_code}/translations/{locale}")
def upsert_crop_translation_endpoint(
    crop_code: str,
    locale: str,
    payload: CropTranslationUpsertRequest,
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.upsert_crop_translation(context, crop_code, locale, payload)


# --- Observation monitor ----------------------------------------------------


@router.get("/observations/summary", response_model=ObservationSummaryOut)
def observations_summary_endpoint(context: RequestContext = Depends(get_request_context)):
    return admin_service.get_observations_summary(context)


@router.get("/observations", response_model=list[ObservationListItemOut])
def list_observations_endpoint(
    crop: str | None = Query(default=None),
    status: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: RequestContext = Depends(get_request_context),
):
    return admin_service.list_observations(
        context, crop_code=crop, status=status, from_date=from_date, to_date=to_date, limit=limit, offset=offset
    )


@router.get("/observations/{daily_observation_id}", response_model=ObservationDetailOut)
def get_observation_detail_endpoint(
    daily_observation_id: UUID, context: RequestContext = Depends(get_request_context)
):
    return admin_service.get_observation_detail(context, daily_observation_id)
