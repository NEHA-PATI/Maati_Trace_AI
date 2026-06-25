from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FPOCreateRequest(BaseModel):
    fpo_name: str = Field(..., min_length=2, max_length=200)
    registration_number: str | None = Field(default=None, max_length=100)
    state_name: str = Field(default="Odisha", min_length=2, max_length=100)
    district_name: str = Field(..., min_length=2, max_length=100)
    block_name: str | None = Field(default=None, max_length=100)
    block_code: int | None = Field(default=None, ge=1)
    contact_phone: str | None = Field(default=None, max_length=20)
    contact_email: str | None = Field(default=None, max_length=200)


class FPOResponse(BaseModel):
    fpo_id: UUID
    fpo_name: str
    registration_number: str | None
    state_name: str
    district_name: str
    block_name: str | None
    block_code: int | None
    contact_phone: str | None
    contact_email: str | None
    is_active: bool


class FarmerCreateRequest(BaseModel):
    user_id: UUID | None = None
    fpo_id: UUID | None = None
    full_name: str = Field(..., min_length=2, max_length=200)
    phone_number: str | None = Field(default=None, max_length=20)
    gender: str | None = Field(default=None, max_length=30)
    state_name: str = Field(default="Odisha", min_length=2, max_length=100)
    district_name: str = Field(..., min_length=2, max_length=100)
    block_name: str | None = Field(default=None, max_length=100)
    block_code: int | None = Field(default=None, ge=1)
    village_name: str | None = Field(default=None, max_length=150)


class FarmerResponse(BaseModel):
    farmer_id: UUID
    user_id: UUID | None
    fpo_id: UUID | None
    full_name: str
    phone_number: str | None
    gender: str | None
    state_name: str
    district_name: str
    district_code: int | None
    block_name: str | None
    block_code: int | None
    village_name: str | None
    is_active: bool


class FarmRegisterRequest(BaseModel):
    farmer_id: UUID
    fpo_id: UUID | None = None
    farm_name: str | None = Field(default=None, max_length=150)
    survey_number: str | None = Field(default=None, max_length=100)
    state_name: str = Field(default="Odisha", min_length=2, max_length=100)
    district_name: str = Field(..., min_length=2, max_length=100)
    block_name: str | None = Field(default=None, max_length=100)
    block_code: int | None = Field(default=None, ge=1)
    village_name: str | None = Field(default=None, max_length=150)
    polygon: dict[str, Any]
    h3_resolution: int = Field(default=12, ge=7, le=12)


class FarmResponse(BaseModel):
    farm_id: UUID
    farmer_id: UUID
    fpo_id: UUID | None
    farm_name: str | None
    survey_number: str | None
    state_name: str
    district_name: str
    district_code: int | None
    block_name: str | None
    block_code: int | None
    village_name: str | None
    polygon_geojson: dict[str, Any]
    h3_resolution: int
    h3_cell_count: int
    area_acres: float | None
    bbox: list[float] | None
    is_active: bool