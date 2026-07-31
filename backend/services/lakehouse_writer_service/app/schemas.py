from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class H3Sentinel2FeatureInput(BaseModel):
    h3_index: int
    pixel_count: int = 0
    valid_pixel_count: int = 0
    cloud_pixel_count: int = 0
    nodata_pixel_count: int = 0
    cloud_percentage: float = 0
    observed_area_m2: float = 0
    valid_area_m2: float = 0
    cloud_area_m2: float = 0
    shadow_area_m2: float = 0
    water_area_m2: float = 0
    snow_area_m2: float = 0
    nodata_area_m2: float = 0
    invalid_area_m2: float = 0
    valid_fraction: float = 0

    fvc_proxy: float | None = None
    nirv: float | None = None

    optical_resolution_m: int = 10
    rededge_swir_resolution_m: int = 20
    processing_version: str = "s2_zonal_v1"

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


class Sentinel2LakehouseWriteRequest(BaseModel):
    farm_id: UUID

    scene_id: str = Field(..., min_length=2)
    scene_datetime: str | None = None
    scene_cloud_cover: float | None = None

    h3_resolution: int = Field(default=12, ge=7, le=12)
    source_assets_used: list[str] = []

    features: list[H3Sentinel2FeatureInput]


class Sentinel2LakehouseWriteResponse(BaseModel):
    dataset: str
    farm_id: UUID
    farmer_id: UUID
    fpo_id: UUID | None

    snapshot_date: date
    scene_id: str

    row_count: int
    postgres_rows_written: int
    parquet_rows_written: int

    storage_mode: str
    parquet_uri: str