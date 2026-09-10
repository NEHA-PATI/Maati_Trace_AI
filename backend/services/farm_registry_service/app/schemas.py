from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class HealthResponse(StrictModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class FarmRegisterRequest(StrictModel):
    farmer_id: UUID
    fpo_id: UUID | None = None
    farm_name: str | None = Field(default=None, max_length=150)
    survey_number: str | None = Field(default=None, max_length=100)
    state_name: str = Field(default="Odisha", min_length=2, max_length=100)
    district_name: str = Field(min_length=2, max_length=100)
    block_name: str | None = Field(default=None, max_length=100)
    block_code: int | None = Field(default=None, ge=1)
    village_name: str | None = Field(default=None, max_length=150)
    crop_code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_\-]+$")
    crop_variety: str | None = Field(default=None, max_length=120)
    crop_stage: str | None = Field(default=None, max_length=120)
    planting_date: date | None = None
    polygon: dict[str, Any]
    h3_resolution: int = Field(default=12, ge=7, le=12)

    @field_validator(
        "farm_name",
        "survey_number",
        "state_name",
        "district_name",
        "block_name",
        "village_name",
        "crop_code",
        "crop_variety",
        "crop_stage",
    )
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None

    @model_validator(mode="after")
    def validate_polygon_shape(self):
        geometry_type = self.polygon.get("type")
        if geometry_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Farm boundary must be a Polygon or MultiPolygon.")
        return self


class FarmResponse(StrictModel):
    farm_id: UUID
    farmer_id: UUID
    fpo_id: UUID | None = None
    farm_name: str | None = None
    survey_number: str | None = None
    state_name: str
    district_name: str
    district_code: int | None = None
    block_name: str | None = None
    block_code: int | None = None
    village_name: str | None = None
    crop_code: str | None = None
    crop_name: str | None = None
    crop_variety: str | None = None
    crop_stage: str | None = None
    planting_date: date | None = None
    polygon_geojson: dict[str, Any]
    h3_resolution: int
    h3_cell_count: int
    area_acres: Decimal | None = None
    bbox: list[float] | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InternalFarmResponse(FarmResponse):
    h3_cells: list[int]


class FarmerFarmSummaryResponse(StrictModel):
    farmer_id: UUID
    farm_count: int
    total_area_acres: Decimal
    state_name: str | None = None
    district_name: str | None = None
    block_name: str | None = None


class FpoFarmSummaryResponse(StrictModel):
    fpo_id: UUID
    farmer_count: int
    farm_count: int
    total_area_acres: Decimal
