from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Crops
# ---------------------------------------------------------------------------


class AdminCropOut(BaseModel):
    crop_id: UUID
    crop_code: str
    lifecycle_type: str
    default_stage_strategy: str
    is_active: bool
    display_order: int
    translations: list[dict] = Field(default_factory=list)


class AdminCropCreateRequest(BaseModel):
    crop_code: str = Field(..., max_length=80)
    lifecycle_type: str = Field(..., pattern="^(ANNUAL|PERENNIAL)$")
    default_stage_strategy: str = Field(..., pattern="^(FIRST_STAGE|CURRENT_STAGE|SYSTEM_SUGGESTED)$")
    display_order: int = 0


class AdminCropUpdateRequest(BaseModel):
    lifecycle_type: str | None = Field(default=None, pattern="^(ANNUAL|PERENNIAL)$")
    default_stage_strategy: str | None = Field(
        default=None, pattern="^(FIRST_STAGE|CURRENT_STAGE|SYSTEM_SUGGESTED)$"
    )
    is_active: bool | None = None
    display_order: int | None = None


# ---------------------------------------------------------------------------
# Configuration versions
# ---------------------------------------------------------------------------


class AdminConfigVersionOut(BaseModel):
    config_version_id: UUID
    crop_id: UUID
    version_number: int
    status: str
    created_at: datetime
    published_at: datetime | None


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


class AdminStageOut(BaseModel):
    stage_id: UUID
    config_version_id: UUID
    stage_code: str
    display_order: int
    is_initial: bool
    is_enabled: bool
    expected_start_day: int | None
    expected_end_day: int | None
    translations: list[dict] = Field(default_factory=list)


class AdminStageCreateRequest(BaseModel):
    stage_code: str = Field(..., max_length=80)
    display_order: int = 0
    is_initial: bool = False


class AdminStageUpdateRequest(BaseModel):
    display_order: int | None = None
    is_initial: bool | None = None
    is_enabled: bool | None = None
    expected_start_day: int | None = None
    expected_end_day: int | None = None


class ReorderRequest(BaseModel):
    order: list[UUID]


# ---------------------------------------------------------------------------
# Stage practices
# ---------------------------------------------------------------------------


class AdminPracticeTemplateOut(BaseModel):
    practice_template_id: UUID
    practice_code: str
    system_type: str
    is_active: bool
    translations: list[dict] = Field(default_factory=list)


class AdminStagePracticeOut(BaseModel):
    stage_practice_id: UUID
    stage_id: UUID
    practice_template_id: UUID
    practice_code: str
    availability_scope: str
    display_order: int
    is_enabled: bool
    media_config: dict = Field(default_factory=dict)
    translations: list[dict] = Field(default_factory=list)


class AdminStagePracticeCreateRequest(BaseModel):
    practice_code: str = Field(..., max_length=80)
    availability_scope: str = Field(default="STAGE_SPECIFIC", pattern="^(STAGE_SPECIFIC|ALWAYS_AVAILABLE)$")
    display_order: int = 0
    media_config: dict = Field(default_factory=dict)


class AdminStagePracticeUpdateRequest(BaseModel):
    availability_scope: str | None = Field(default=None, pattern="^(STAGE_SPECIFIC|ALWAYS_AVAILABLE)$")
    display_order: int | None = None
    is_enabled: bool | None = None
    media_config: dict | None = None


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------

FIELD_TYPE_PATTERN = (
    "^(BOOLEAN|YES_NO_UNKNOWN|SINGLE_CHOICE|MULTI_CHOICE|PICTURE_CHOICE|SEVERITY|"
    "QUANTITY_UNIT|NUMBER|SHORT_TEXT|PRODUCT|PEST|DISEASE|APPLICATION_AREA)$"
)


class AdminFieldOut(BaseModel):
    field_definition_id: UUID
    stage_practice_id: UUID
    field_code: str
    field_type: str
    semantic_type: str | None
    display_order: int
    is_required: bool
    is_enabled: bool
    translations: list[dict] = Field(default_factory=list)


class AdminFieldCreateRequest(BaseModel):
    field_code: str = Field(..., max_length=100)
    field_type: str = Field(..., pattern=FIELD_TYPE_PATTERN)
    semantic_type: str | None = Field(default=None, max_length=80)
    display_order: int = 0
    is_required: bool = False


class AdminFieldUpdateRequest(BaseModel):
    field_type: str | None = Field(default=None, pattern=FIELD_TYPE_PATTERN)
    semantic_type: str | None = None
    display_order: int | None = None
    is_required: bool | None = None
    is_enabled: bool | None = None


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class AdminOptionOut(BaseModel):
    field_option_id: UUID
    field_definition_id: UUID
    option_code: str
    display_order: int
    icon_key: str | None
    is_active: bool
    translations: list[dict] = Field(default_factory=list)


class AdminOptionCreateRequest(BaseModel):
    option_code: str = Field(..., max_length=100)
    display_order: int = 0


class AdminOptionUpdateRequest(BaseModel):
    display_order: int | None = None
    icon_key: str | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------


class CropTranslationUpsertRequest(BaseModel):
    display_name: str = Field(..., max_length=150)
    short_description: str | None = Field(default=None, max_length=500)


class StageTranslationUpsertRequest(BaseModel):
    display_name: str = Field(..., max_length=150)
    short_description: str | None = Field(default=None, max_length=1000)
    instruction_text: str | None = Field(default=None, max_length=1200)


class PracticeTranslationUpsertRequest(BaseModel):
    display_name: str = Field(..., max_length=150)
    help_text: str | None = Field(default=None, max_length=700)


class FieldTranslationUpsertRequest(BaseModel):
    label: str = Field(..., max_length=200)
    help_text: str | None = Field(default=None, max_length=500)


class OptionTranslationUpsertRequest(BaseModel):
    label: str = Field(..., max_length=150)


# ---------------------------------------------------------------------------
# Validation / publish
# ---------------------------------------------------------------------------


class ValidationIssue(BaseModel):
    code: str
    stage_code: str | None = None
    practice_code: str | None = None
    field_code: str | None = None
    locale: str | None = None


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Observation monitor
# ---------------------------------------------------------------------------


class ObservationSummaryOut(BaseModel):
    total_observations: int
    serious_count: int
    today_count: int
    open_review_flags: int


class ObservationListItemOut(BaseModel):
    daily_observation_id: UUID
    crop_cycle_id: UUID
    stage_code: str
    observed_on: date
    crop_status: str
    created_at: datetime
    farm_id: UUID
    farmer_user_id: UUID
    crop_code: str


class ObservationDetailOut(ObservationListItemOut):
    updated_at: datetime
    practices: list[dict] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# TTS / instruction audio
# ---------------------------------------------------------------------------


class TtsStatusOut(BaseModel):
    enabled: bool
    provider: str
    model_id: str
    api_key_configured: bool


class TtsVoiceOut(BaseModel):
    voice_id: str
    name: str
    language: str | None = None
    preview_url: str | None = None


class TtsProfileOut(BaseModel):
    tts_profile_id: UUID
    profile_code: str
    locale: str
    provider: str
    model_id: str
    voice_id: str
    voice_name: str | None
    output_format: dict = Field(default_factory=dict)
    generation_config: dict = Field(default_factory=dict)
    is_active: bool


class TtsProfileUpsertRequest(BaseModel):
    voice_id: str = Field(..., min_length=1, max_length=150)
    voice_name: str | None = Field(default=None, max_length=200)
    model_id: str | None = Field(default=None, max_length=100)
    speed: float | None = None
    volume: float | None = None


class InstructionAudioGenerateRequest(BaseModel):
    force: bool = False


class InstructionAudioGenerateResponse(BaseModel):
    stage_id: UUID
    locale: str
    status: str
    asset_id: UUID | None = None
    content_url: str | None = None
