from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FeatureMaterializeRequest(StrictModel):
    start_date: date
    end_date: date
    latest_only: bool = False
    force_refresh: bool = False

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        if (self.end_date - self.start_date).days > 1095:
            raise ValueError("One feature-materialization request is limited to 1095 days")
        return self


class CalculationMaterializeRequest(StrictModel):
    start_date: date | None = None
    end_date: date | None = None
    latest_only: bool = False

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        return self


class IntelligenceMaterializeRequest(FeatureMaterializeRequest):
    pass


class CropProfileCreateRequest(StrictModel):
    crop_code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_\-]+$")
    crop_name: str = Field(min_length=2, max_length=150)
    profile_version: str = Field(min_length=2, max_length=80)
    crop_type: str = Field(default="crop", max_length=50)
    minimum_history_days: int = Field(default=60, ge=0, le=3650)
    preferred_history_days: int = Field(default=180, ge=0, le=3650)
    temporal_windows: dict[str, Any] = {}
    root_zone_weights: dict[str, float] = {}
    soil_ranges: dict[str, Any] = {}
    normalization: dict[str, Any] = {}
    growth_config: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    @model_validator(mode="after")
    def check_profile(self):
        if self.preferred_history_days < self.minimum_history_days:
            raise ValueError("preferred_history_days must be >= minimum_history_days")
        if self.root_zone_weights:
            total = sum(float(v) for v in self.root_zone_weights.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError("root_zone_weights must sum to 1.0")
        return self


class CropProfileUpdateRequest(StrictModel):
    crop_name: str = Field(min_length=2, max_length=150)
    crop_type: str = Field(default="crop", max_length=50)
    minimum_history_days: int = Field(default=60, ge=0, le=3650)
    preferred_history_days: int = Field(default=180, ge=0, le=3650)
    temporal_windows: dict[str, Any] = {}
    root_zone_weights: dict[str, float] = {}
    soil_ranges: dict[str, Any] = {}
    normalization: dict[str, Any] = {}
    growth_config: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    @model_validator(mode="after")
    def check_profile(self):
        if self.preferred_history_days < self.minimum_history_days:
            raise ValueError("preferred_history_days must be >= minimum_history_days")
        if self.root_zone_weights:
            total = sum(float(v) for v in self.root_zone_weights.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError("root_zone_weights must sum to 1.0")
        return self


class FormulaCreateRequest(StrictModel):
    crop_code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_\-]+$")
    prediction_key: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9_\-]+$")
    display_name: str = Field(min_length=2, max_length=150)
    formula_version: str = Field(min_length=2, max_length=100)
    crop_profile_version: str = Field(min_length=2, max_length=100)
    formula_type: Literal["weighted_components"] = "weighted_components"
    score_direction: Literal["risk", "condition"]
    execution_order: int = Field(default=100, ge=1, le=10000)
    component_weights: dict[str, float]
    thresholds: dict[str, float] = {}
    parameters: dict[str, Any] = {}
    description: str | None = None
    metadata: dict[str, Any] = {}

    @model_validator(mode="after")
    def check_weights(self):
        if not self.component_weights:
            raise ValueError("component_weights is required")
        if any(float(v) < 0 for v in self.component_weights.values()):
            raise ValueError("component weights cannot be negative")
        total = sum(float(v) for v in self.component_weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError("component_weights must sum to 1.0")
        return self


class FormulaUpdateRequest(StrictModel):
    display_name: str = Field(min_length=2, max_length=150)
    crop_profile_version: str = Field(min_length=2, max_length=100)
    formula_type: Literal["weighted_components"] = "weighted_components"
    score_direction: Literal["risk", "condition"]
    execution_order: int = Field(default=100, ge=1, le=10000)
    component_weights: dict[str, float]
    thresholds: dict[str, float] = {}
    parameters: dict[str, Any] = {}
    description: str | None = None
    metadata: dict[str, Any] = {}

    @model_validator(mode="after")
    def check_weights(self):
        if not self.component_weights:
            raise ValueError("component_weights is required")
        total = sum(float(v) for v in self.component_weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError("component_weights must sum to 1.0")
        return self


class CloneVersionRequest(StrictModel):
    new_version: str = Field(min_length=2, max_length=100)


class SeedFormulasRequest(StrictModel):
    source_crop_code: str = Field(min_length=2, max_length=80)
    formula_version_suffix: str = Field(default="v1", min_length=1, max_length=50)


class CloneCropRequest(StrictModel):
    source_crop_code: str = Field(min_length=2, max_length=80)
    target_crop_code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_\-]+$")
    target_crop_name: str = Field(min_length=2, max_length=150)
    target_profile_version: str = Field(min_length=2, max_length=100)
    formula_version_suffix: str = Field(default="v1", min_length=1, max_length=50)


class MetricContentUpdateRequest(StrictModel):
    display_name: str = Field(min_length=2, max_length=150)
    signal_meaning: str = Field(min_length=2, max_length=2000)
    ranges: dict[str, Any] = {}
    messages: dict[str, Any] = {}
    field_interpretation: dict[str, Any] = {}


class ProcessingTriggerRequest(StrictModel):
    farm_id: str
    start_date: date
    end_date: date
    latest_only: bool = False
    force_refresh: bool = False
