from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class RasterAsset(BaseModel):
    key: str
    href: str
    title: str | None = None
    media_type: str | None = None
    roles: list[str] = []
    common_name: str | None = None


class Sentinel2Scene(BaseModel):
    provider: str = "planetary_computer"
    collection_id: str
    scene_id: str
    datetime: str | None = None
    cloud_cover: float | None = None
    properties: dict[str, Any] = {}
    assets: list[RasterAsset]


class Sentinel2IndicesPreviewRequest(BaseModel):
    farm_id: str | None = None
    scene: Sentinel2Scene
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    h3_resolution: int = Field(default=12, ge=7, le=12)


class H3Sentinel2Feature(BaseModel):
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


class Sentinel2IndicesPreviewResponse(BaseModel):
    farm_id: str | None
    provider: str
    collection_id: str
    scene_id: str
    scene_datetime: str | None
    scene_cloud_cover: float | None
    bbox: list[float]
    h3_resolution: int
    source_assets_used: list[str]
    row_count: int
    total_pixel_count: int
    total_valid_pixel_count: int
    total_cloud_pixel_count: int
    features: list[H3Sentinel2Feature]

class Sentinel2IndicesFromSearchRequest(BaseModel):
    farm_id: str | None = None
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    h3_resolution: int = Field(default=12, ge=7, le=12)

    provider: str = "planetary_computer"
    collection_id: str = "sentinel-2-l2a"
    start_date: str
    end_date: str
    max_cloud_cover: float | None = Field(default=30, ge=0, le=100)