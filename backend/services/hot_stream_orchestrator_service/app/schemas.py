from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class FarmAnalysisMaterializeRequest(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    max_cloud_cover: float | None = Field(default=30, ge=0, le=100)
    h3_resolution: int = Field(default=12, ge=7, le=12)
    min_valid_pixel_percentage: float = 1.0
    max_candidate_scenes: int = 10

    provider: str = "planetary_computer"
    collection_id: str = "sentinel-2-l2a"

    # For first production stage keep this true.
    # It uses a small bbox around farm bbox center to avoid large compute.
    use_tiny_preview_bbox: bool = True
    tiny_bbox_size_deg: float = Field(default=0.00020, gt=0, le=0.01)

    force_refresh: bool = False


class FarmAnalysisMaterializeResponse(BaseModel):
    farm_id: UUID
    farmer_id: UUID
    fpo_id: UUID | None

    district_name: str
    block_name: str | None
    block_code: int | None

    scene_id: str
    scene_datetime: str | None
    scene_cloud_cover: float | None

    raster_row_count: int
    raster_total_pixel_count: int
    raster_total_valid_pixel_count: int
    raster_total_cloud_pixel_count: int

    lakehouse_dataset: str
    lakehouse_row_count: int
    postgres_rows_written: int
    parquet_rows_written: int
    parquet_uri: str

    status: Literal["materialized"]
    details: dict[str, Any] = {}