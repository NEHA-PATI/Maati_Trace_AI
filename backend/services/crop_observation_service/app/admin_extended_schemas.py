from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AdminOverviewOut(BaseModel):
    records: int = 0
    farmers: int = 0
    farms: int = 0
    serious_stage_updates: int = 0
    some_problem_stage_updates: int = 0
    good_stage_updates: int = 0
    open_reviews: int = 0
    high_severity_records: int = 0
    open_flags: int = 0
    issue_images: int = 0
    practice_images: int = 0
    crop_condition_images: int = 0
    voice_notes: int = 0
    by_crop: list[dict[str, Any]] = Field(default_factory=list)
    by_practice: list[dict[str, Any]] = Field(default_factory=list)
    trend: list[dict[str, Any]] = Field(default_factory=list)


class AdminPracticeRecordOut(BaseModel):
    record_id: UUID
    daily_observation_id: UUID
    crop_cycle_id: UUID
    farm_crop_id: UUID
    farmer_user_id: UUID
    farm_id: UUID
    crop_code: str
    season_year: int | None = None
    season_name: str | None = None
    config_version_id: UUID
    stage_code: str
    observed_on: date
    crop_status: str
    stage_practice_id: UUID
    practice_code: str
    answers: dict[str, Any] = Field(default_factory=dict)
    completion_status: str
    severity: str | None = None
    issue_code: str | None = None
    review_status: str
    admin_note: str | None = None
    reviewed_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    issue_image_count: int = 0
    practice_image_count: int = 0
    voice_count: int = 0


class AdminRecordMediaOut(BaseModel):
    media_asset_id: UUID
    media_type: str
    mime_type: str
    byte_size: int
    duration_seconds: float | None = None
    media_role: str
    media_purpose: str
    slot_number: int | None = None
    content_url: str


class AdminRecordDetailOut(AdminPracticeRecordOut):
    media: list[AdminRecordMediaOut] = Field(default_factory=list)
    revisions: list[dict[str, Any]] = Field(default_factory=list)


class RecordReviewUpdateRequest(BaseModel):
    review_status: Literal[
        "NEW",
        "IN_REVIEW",
        "NEEDS_FOLLOW_UP",
        "REVIEWED",
        "RESOLVED",
    ]
    admin_note: str | None = Field(default=None, max_length=4000)


class RecordReviewOut(BaseModel):
    review_id: UUID
    record_type: str
    record_id: UUID
    review_status: str
    admin_note: str | None = None
    reviewed_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class SystemMediaUploadRequest(BaseModel):
    target_type: Literal["CROP", "STAGE", "STAGE_PRACTICE", "FIELD_OPTION"]
    target_id: UUID
    asset_role: Literal[
        "CROP_CARD_IMAGE",
        "STAGE_IMAGE",
        "INSTRUCTION_AUDIO",
        "PRACTICE_GUIDE_IMAGE",
        "OPTION_IMAGE",
    ]
    locale: str | None = Field(default=None, max_length=10)
    mime_type: str = Field(min_length=3, max_length=150)
    byte_size: int = Field(gt=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    original_filename: str | None = Field(default=None, max_length=500)
    slot_number: int | None = Field(default=None, ge=1, le=10)


class SystemMediaUploadResponse(BaseModel):
    asset_id: UUID
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class SystemMediaBindingOut(BaseModel):
    binding_id: UUID
    asset_id: UUID
    target_type: str
    target_id: UUID
    asset_role: str
    locale: str | None = None
    slot_number: int | None = None
    is_active: bool = True
    mime_type: str | None = None
    byte_size: int | None = None
    duration_seconds: float | None = None
    storage_backend: str | None = None
    object_key: str | None = None
    upload_status: str | None = None
    original_filename: str | None = None
    content_url: str | None = None


class SystemMediaCompleteResponse(BaseModel):
    asset_id: UUID
    binding: SystemMediaBindingOut
    content_url: str


class TtsBatchRequest(BaseModel):
    locales: list[str] = Field(default_factory=lambda: ["en-IN", "or-IN"], min_length=1, max_length=2)
    force: bool = False

    @field_validator("locales")
    @classmethod
    def unique_locales(cls, value: list[str]) -> list[str]:
        result = []
        for item in value:
            if item not in result:
                result.append(item)
        return result


class TtsBatchItemOut(BaseModel):
    stage_id: UUID
    locale: str
    status: str
    asset_id: UUID | None = None
    error_code: str | None = None
    error_message: str | None = None


class TtsBatchOut(BaseModel):
    total: int
    ready: int
    failed: int
    items: list[TtsBatchItemOut]


class AdminSystemStatusOut(BaseModel):
    service: str
    environment: str
    storage_backend: str
    s3_bucket_configured: bool
    s3_bucket: str | None = None
    tts_enabled: bool
    cartesia_key_configured: bool
    tts_model: str
    system_assets_ready: int = 0
    system_assets_requested: int = 0
    tts_ready: int = 0
    tts_failed: int = 0
    outbox_pending: int = 0
    open_flags: int = 0


class AdminDiagnosticCheckOut(BaseModel):
    status: str
    message: str


class AdminDiagnosticsOut(BaseModel):
    database: AdminDiagnosticCheckOut
    storage: AdminDiagnosticCheckOut
    cartesia: AdminDiagnosticCheckOut
    farm_registry: AdminDiagnosticCheckOut
