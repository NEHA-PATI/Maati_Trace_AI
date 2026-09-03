from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

CROP_STATUS_OPTIONS = ("GOOD", "SOME_PROBLEM", "SERIOUS_PROBLEM")


class HealthResponse(BaseModel):
    service: str
    status: str
    environment: str


# ---------------------------------------------------------------------------
# Crop catalogue
# ---------------------------------------------------------------------------


class CropSummary(BaseModel):
    crop_code: str
    lifecycle_type: str
    name: str
    secondary_name: str | None = None
    image_url: str | None = None


class CropListResponse(BaseModel):
    items: list[CropSummary]


# ---------------------------------------------------------------------------
# Farm crops
# ---------------------------------------------------------------------------


class FarmCropCreateRequest(BaseModel):
    crop_code: str = Field(..., max_length=80)
    variety_name: str | None = Field(default=None, max_length=200)
    planted_on: date | None = None


class FarmCropResponse(BaseModel):
    farm_crop_id: UUID
    farm_id: UUID
    farmer_user_id: UUID
    crop_code: str
    variety_name: str | None
    planted_on: date | None
    status: str
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Crop cycles
# ---------------------------------------------------------------------------


class CropCycleCreateRequest(BaseModel):
    season_year: int | None = None
    season_name: str | None = Field(default=None, max_length=100)


class CropCycleResponse(BaseModel):
    crop_cycle_id: UUID
    farm_crop_id: UUID
    config_version_id: UUID
    season_year: int | None
    season_name: str | None
    cycle_started_on: date
    cycle_ended_on: date | None
    current_stage_code: str | None
    current_stage_source: str | None
    status: str


# ---------------------------------------------------------------------------
# Screen API
# ---------------------------------------------------------------------------


class ScreenCropOut(BaseModel):
    crop_code: str
    name: str
    secondary_name: str | None = None
    image_url: str | None = None


class ScreenFarmOut(BaseModel):
    farm_id: UUID
    farm_name: str | None = None


class ScreenCycleOut(BaseModel):
    crop_cycle_id: UUID
    current_stage_code: str | None = None


class ScreenStageOut(BaseModel):
    stage_code: str
    name: str
    secondary_name: str | None = None
    short_description: str | None = None
    image_url: str | None = None
    instruction_audio_url: str | None = None
    instruction_audio_duration_seconds: float | None = None


class ScreenStageTabOut(BaseModel):
    stage_code: str
    name: str
    display_order: int
    is_current: bool


class ScreenTodayOut(BaseModel):
    date: date
    observation: dict | None = None


class ScreenCropStatusOptionOut(BaseModel):
    code: str


class ScreenPracticeFieldOut(BaseModel):
    field_code: str
    field_type: str
    label: str
    help_text: str | None = None
    is_required: bool
    display_order: int
    options: list[dict] = Field(default_factory=list)


class ScreenPracticeOut(BaseModel):
    practice_code: str
    name: str
    display_order: int
    media_config: dict[str, Any] = Field(default_factory=dict)
    fields: list[ScreenPracticeFieldOut] = Field(default_factory=list)


class RecentHistoryItem(BaseModel):
    daily_observation_id: UUID
    date: date
    crop_status: str
    stage_code: str
    media_summary: dict[str, Any] = Field(default_factory=dict)


class ScreenResponse(BaseModel):
    crop: ScreenCropOut
    farm: ScreenFarmOut
    cycle: ScreenCycleOut
    stage: ScreenStageOut
    stage_tabs: list[ScreenStageTabOut]
    today: ScreenTodayOut
    crop_status_options: list[ScreenCropStatusOptionOut]
    practices: list[ScreenPracticeOut]
    recent_history: list[RecentHistoryItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Daily status save
# ---------------------------------------------------------------------------


class DailyStatusSaveRequest(BaseModel):
    client_entry_id: UUID
    crop_status: str = Field(..., pattern="^(GOOD|SOME_PROBLEM|SERIOUS_PROBLEM)$")
    captured_at_client: datetime | None = None


class DailyStatusResponse(BaseModel):
    daily_observation_id: UUID
    crop_cycle_id: UUID
    stage_code: str
    observed_on: date
    crop_status: str
    client_entry_id: UUID
    sync_source: str
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Practice observation save
# ---------------------------------------------------------------------------


class PracticeSaveRequest(BaseModel):
    client_entry_id: UUID
    answers: dict[str, Any] = Field(default_factory=dict)


class PracticeObservationResponse(BaseModel):
    practice_observation_id: UUID
    daily_observation_id: UUID
    practice_code: str
    answers: dict[str, Any]
    completion_status: str
    client_entry_id: UUID
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


class MediaUploadRequest(BaseModel):
    owner_type: str = Field(..., pattern="^(DAILY_STAGE|PRACTICE)$")
    owner_id: UUID
    media_type: str = Field(..., pattern="^(IMAGE|AUDIO)$")
    media_purpose: str = Field(default="GENERAL", pattern="^(GENERAL|CROP_CONDITION|ISSUE_EVIDENCE|PRACTICE_EVIDENCE)$")
    mime_type: str = Field(..., max_length=150)
    byte_size: int = Field(..., gt=0)
    duration_seconds: float | None = None


class MediaUploadResponse(BaseModel):
    media_asset_id: UUID
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class MediaAssetResponse(BaseModel):
    media_asset_id: UUID
    media_type: str
    mime_type: str
    byte_size: int
    duration_seconds: float | None
    upload_status: str
    content_url: str | None = None


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


class HistoryMediaSummary(BaseModel):
    crop_condition: dict[str, Any] = Field(default_factory=dict)
    issue_evidence: dict[str, Any] = Field(default_factory=dict)
    practice_evidence: dict[str, Any] = Field(default_factory=dict)
    voice_note: dict[str, Any] = Field(default_factory=dict)


class HistoryItem(BaseModel):
    daily_observation_id: UUID
    date: date
    crop_status: str
    stage_code: str
    practices: list[dict[str, Any]] = Field(default_factory=list)
    media_summary: HistoryMediaSummary


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    next_cursor: str | None = None


# ---------------------------------------------------------------------------
# Per-practice history (shown as compact rows above the "new update" form —
# see PracticeSheet.jsx)
# ---------------------------------------------------------------------------


class PracticeHistoryItem(BaseModel):
    practice_observation_id: UUID
    observed_on: date
    answers: dict[str, Any]
    summary_values: list[str] = Field(default_factory=list)
    media: HistoryMediaSummary


class PracticeHistoryResponse(BaseModel):
    items: list[PracticeHistoryItem]
