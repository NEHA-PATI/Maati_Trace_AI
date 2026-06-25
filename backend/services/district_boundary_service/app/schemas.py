from pydantic import BaseModel, Field


class StateResponse(BaseModel):
    state_code: int
    state_name: str


class DistrictResponse(BaseModel):
    district_code: int
    district_name: str
    state_code: int
    state_name: str


class BlockResponse(BaseModel):
    block_code: int
    block_name: str
    district_code: int | None
    district_name: str
    state_code: int | None
    state_name: str | None


class LocationValidateRequest(BaseModel):
    state_name: str = Field(default="Odisha", min_length=2, max_length=100)
    district_name: str = Field(..., min_length=2, max_length=100)
    block_name: str | None = Field(default=None, min_length=2, max_length=100)
    block_code: int | None = Field(default=None, ge=1)


class LocationValidateResponse(BaseModel):
    is_valid: bool
    state_name: str
    district_name: str
    district_code: int | None
    block_name: str | None
    block_code: int | None
    message: str


class ServiceStatsResponse(BaseModel):
    states_count: int
    districts_count: int
    blocks_count: int