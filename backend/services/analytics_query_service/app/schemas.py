from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class H3Sentinel2FeatureResponse(BaseModel):
    feature_id: UUID
    farm_id: UUID
    farmer_id: UUID
    fpo_id: UUID | None

    state_name: str
    district_name: str
    district_code: int | None
    block_name: str | None
    block_code: int | None

    snapshot_date: date
    scene_id: str
    scene_datetime: datetime | None
    scene_cloud_cover: float | None

    h3_resolution: int
    h3_index: int

    pixel_count: int
    valid_pixel_count: int
    cloud_pixel_count: int
    nodata_pixel_count: int
    cloud_percentage: float

    mean_blue: float | None = None
    mean_green: float | None = None
    mean_red: float | None = None
    mean_rededge1: float | None = None
    mean_rededge2: float | None = None
    mean_rededge3: float | None = None
    mean_nir: float | None = None
    mean_nir08: float | None = None
    mean_swir16: float | None = None
    mean_swir22: float | None = None

    ndvi: float | None = None
    gndvi: float | None = None
    evi: float | None = None
    savi: float | None = None

    ndmi: float | None = None
    ndwi: float | None = None
    mndwi: float | None = None
    msi: float | None = None

    bsi: float | None = None
    nbr: float | None = None
    nbr2: float | None = None

    ndre: float | None = None
    reci: float | None = None

    source_assets_used: list[str]
    parquet_uri: str | None
    created_at: datetime


class FarmSentinel2LatestResponse(BaseModel):
    farm_id: UUID
    farmer_id: UUID
    fpo_id: UUID | None

    district_name: str
    block_name: str | None
    block_code: int | None

    snapshot_date: date
    scene_id: str
    scene_datetime: datetime | None
    scene_cloud_cover: float | None

    row_count: int
    total_pixel_count: int
    total_valid_pixel_count: int
    total_cloud_pixel_count: int
    avg_cloud_percentage: float | None

    avg_ndvi: float | None
    avg_gndvi: float | None
    avg_evi: float | None
    avg_savi: float | None
    avg_ndmi: float | None
    avg_ndwi: float | None
    avg_mndwi: float | None
    avg_msi: float | None
    avg_bsi: float | None
    avg_nbr: float | None
    avg_nbr2: float | None
    avg_ndre: float | None
    avg_reci: float | None

    features: list[H3Sentinel2FeatureResponse]


class FarmSentinel2HistoryItem(BaseModel):
    farm_id: UUID
    snapshot_date: date
    scene_id: str
    scene_datetime: datetime | None
    scene_cloud_cover: float | None

    row_count: int
    total_pixel_count: int
    total_valid_pixel_count: int
    total_cloud_pixel_count: int
    avg_cloud_percentage: float | None

    avg_ndvi: float | None
    avg_ndmi: float | None
    avg_ndwi: float | None
    avg_bsi: float | None


class FarmSentinel2HistoryResponse(BaseModel):
    farm_id: UUID
    item_count: int
    items: list[FarmSentinel2HistoryItem]


class FarmIntelligenceSummaryResponse(BaseModel):
    farm_id: UUID
    has_analysis: bool
    analysis_mode: str | None = None
    usable_scene_max_cloud_percentage: float | None = None
    latest_snapshot_date: date | None = None
    latest_scene_id: str | None = None

    vegetation_signal: str | None = None
    moisture_signal: str | None = None
    bare_soil_signal: str | None = None
    data_quality_signal: str | None = None

    avg_ndvi: float | None = None
    avg_ndmi: float | None = None
    avg_bsi: float | None = None
    avg_cloud_percentage: float | None = None
    weighted_ndvi: float | None = None
    weighted_ndmi: float | None = None
    weighted_ndwi: float | None = None
    weighted_bsi: float | None = None
    weighted_evi: float | None = None
    weighted_savi: float | None = None
    weighted_msi: float | None = None
    weighted_nbr: float | None = None
    weighted_ndre: float | None = None
    weighted_surface_temp_c: float | None = None
    valid_pixel_percentage: float | None = None
    total_h3_cells: int | None = None
    total_farm_h3_cells: int | None = None
    processed_h3_cells: int | None = None
    latest_processed_h3_cells: int | None = None
    total_grid_cells: int | None = None
    grid_cells_with_values: int | None = None
