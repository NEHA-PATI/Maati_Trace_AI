from typing import Any, Literal

from pydantic import BaseModel, Field


class DatasetRegistryItem(BaseModel):
    dataset_key: str
    display_name: str
    priority: int
    category: str
    providers: dict[str, list[str]]
    expected_assets: list[str]
    derived_features: list[str]
    maatitrace_use: list[str]
    hot_stream_use: bool
    cold_batch_use: bool
    compute_frequency: str


class ProviderCollectionResponse(BaseModel):
    provider: str
    stac_url: str
    collection_count: int
    collections: list[dict[str, Any]]


class DatasetAvailabilityRequest(BaseModel):
    provider: str = Field(default="planetary_computer")


class DatasetAvailabilityItem(BaseModel):
    dataset_key: str
    display_name: str
    provider: str
    candidate_collection_ids: list[str]
    available_collection_ids: list[str]
    is_available: bool
    matched_collections: list[dict[str, Any]]


class DatasetAvailabilityResponse(BaseModel):
    provider: str
    datasets: list[DatasetAvailabilityItem]


class CollectionAssetsResponse(BaseModel):
    provider: str
    collection_id: str
    title: str | None = None
    description: str | None = None
    available_asset_keys_from_summaries: list[str]
    summaries: dict[str, Any]


class StacSearchRequest(BaseModel):
    provider: str = Field(default="planetary_computer")
    collection_id: str = Field(..., min_length=2)
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    max_cloud_cover: float | None = Field(default=None, ge=0, le=100)
    limit: int = Field(default=10, ge=1, le=100)


class StacAsset(BaseModel):
    key: str
    href: str
    title: str | None = None
    media_type: str | None = None
    roles: list[str] = []
    common_name: str | None = None
    center_wavelength: float | None = None
    full_width_half_max: float | None = None


class StacSearchItem(BaseModel):
    provider: str
    collection_id: str
    scene_id: str
    datetime: str | None
    bbox: list[float] | None
    cloud_cover: float | None
    properties: dict[str, Any]
    assets: list[StacAsset]


class StacSearchResponse(BaseModel):
    provider: str
    collection_id: str
    returned_count: int
    items: list[StacSearchItem]


class LatestSceneRequest(BaseModel):
    provider: str = Field(default="planetary_computer")
    collection_id: str = Field(..., min_length=2)
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    start_date: str
    end_date: str
    max_cloud_cover: float | None = Field(default=None, ge=0, le=100)


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str