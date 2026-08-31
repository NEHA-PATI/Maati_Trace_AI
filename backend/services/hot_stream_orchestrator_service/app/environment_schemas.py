from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


DEFAULT_ENVIRONMENT_DATASETS = [
    # Tier A additions. Sentinel-2 stays on existing full-refresh.
    "sentinel_1_rtc",
    "landsat_c2_l2",
    "gpm_imerg",
    "cop_dem_glo30",
    "esa_worldcover",
    "jrc_surface_water",
    # Tier B
    "era5_land",
    "soilgrids_v2",
    "smap_l4_sm",
    "modis_et",
    "modis_lai_fpar",
    "weather_forecast",
]


class EnvironmentRefreshRequest(BaseModel):
    start_date: str
    end_date: str
    dataset_keys: list[str] = Field(default_factory=lambda: list(DEFAULT_ENVIRONMENT_DATASETS))
    max_items_per_dataset: int = Field(default=1, ge=1, le=31)
    max_cloud_cover: float | None = Field(default=40, ge=0, le=100)
    force_refresh: bool = False
    dataset_options: dict[str, dict[str, Any]] = Field(default_factory=dict)


class DatasetStageResult(BaseModel):
    dataset_key: str
    status: str
    provider: str | None = None
    source_items_found: int = 0
    source_items_processed: int = 0
    postgres_rows_written: int = 0
    parquet_rows_written: int = 0
    message: str | None = None


class EnvironmentRefreshResponse(BaseModel):
    farm_id: str
    status: str
    datasets: list[DatasetStageResult]
