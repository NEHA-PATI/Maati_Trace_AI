from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class H3TemporalCellResponse(BaseModel):
    h3_index: int
    h3_resolution: int
    data_status: str
    observation_date: date | None = None
    observation_age_days: int | None = None
    freshness_status: str
    confidence_level: str
    valid_fraction: float
    valid_coverage_percent: float
    scene_id: str | None = None
    processing_version: str | None = None
    ndvi: float | None = None
    ndmi: float | None = None
    bsi: float | None = None
    fvc_proxy: float | None = None
    nirv: float | None = None
    canopy_condition: str
    moisture_condition: str
    soil_exposure_condition: str
    surface_water_signal: str
    previous_observation_date: date | None = None
    observation_interval_days: int | None = None
    ndvi_change: float | None = None
    ndvi_trend: str
    ndmi_change: float | None = None
    moisture_trend: str
    action_priority: str


class H3TemporalMosaicResponse(BaseModel):
    farm_id: UUID
    analysis_mode: Literal["per_h3_latest_valid_temporal_mosaic"]
    rule_version: str
    h3_valid_fraction_threshold: float
    total_h3_cells: int
    h3_cells_with_valid_history: int
    h3_cells_waiting_for_valid_observation: int
    historical_cell_coverage_percent: float
    newest_cell_observation_date: date | None = None
    oldest_cell_observation_date: date | None = None
    mosaic_date_span_days: int | None = None
    farm_weighted_information: dict[str, Any]
    priority_counts: dict[str, int]
    cells: list[H3TemporalCellResponse]

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
