from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


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

    # The legacy Sentinel-2 endpoint may still opt into a tiny preview, but the
    # canonical latest-analysis workflow always overrides this to false so all
    # registered farm H3 cells are processed.
    use_tiny_preview_bbox: bool = True
    tiny_bbox_size_deg: float = Field(default=0.00020, gt=0, le=0.01)

    force_refresh: bool = False


class LatestAnalysisRequest(BaseModel):
    """Input for the single canonical farm intelligence workflow.

    Dates are deliberately optional for the farmer action.  The orchestrator
    searches the most recent usable scene inside a bounded lookback window,
    while retaining an explicit date range for deterministic/admin runs.
    """

    start_date: str = Field(
        default_factory=lambda: (date.today() - timedelta(days=365)).isoformat(),
        description="Earliest acceptable source date, YYYY-MM-DD",
    )
    end_date: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Latest acceptable source date, YYYY-MM-DD",
    )
    max_cloud_cover: float | None = Field(default=40, ge=0, le=100)
    h3_resolution: int = Field(default=12, ge=7, le=12)
    max_items_per_dataset: int = Field(default=1, ge=1, le=31)
    max_candidate_scenes: int = Field(default=10, ge=1, le=50)
    provider: str = "planetary_computer"
    collection_id: str = "sentinel-2-l2a"
    force_refresh: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if start > end:
            raise ValueError("start_date must be <= end_date")
        if (end - start).days > 1095:
            raise ValueError("One latest-analysis request is limited to 1095 days")
        return self


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


class Sentinel2HistoryBackfillRequest(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    max_cloud_cover: float | None = Field(default=40, ge=0, le=100)
    max_scenes: int = Field(default=31, ge=1, le=100)
    provider: str = "planetary_computer"
    collection_id: str = "sentinel-2-l2a"
    force_refresh: bool = False
