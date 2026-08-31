from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ResamplingName = Literal["nearest", "bilinear", "cubic"]
TemporalType = Literal[
    "scene",
    "subdaily",
    "daily",
    "composite",
    "annual",
    "static",
    "forecast",
]
SpatialLevel = Literal["h3", "farm"]


class AssetContract(BaseModel):
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    required: bool = True
    unit: str | None = None
    scale: float | None = None
    offset: float | None = None
    nodata: float | int | None = None
    resampling: ResamplingName = "bilinear"


class ProviderContract(BaseModel):
    source_adapter: Literal["stac", "cmr", "cds", "wcs", "json_api"]
    collection_ids: list[str] = Field(default_factory=list)
    short_name: str | None = None
    version: str | None = None
    priority: int = 1
    enabled: bool = True
    auth_type: str = "none"
    metadata: dict[str, Any] = Field(default_factory=dict)


class StorageContract(BaseModel):
    spatial_level: SpatialLevel
    postgres_table: str
    parquet_dataset: str


class DatasetContract(BaseModel):
    dataset_key: str
    display_name: str
    priority: int
    category: str
    temporal_type: TemporalType
    processor_key: str
    providers: dict[str, ProviderContract]
    assets: list[AssetContract] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    native_resolution_m: float | None = None
    derived_features: list[str] = Field(default_factory=list)
    maatitrace_use: list[str] = Field(default_factory=list)
    hot_stream_use: bool = False
    cold_batch_use: bool = True
    compute_frequency: str
    storage: StorageContract
    processing_version: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    def legacy_dict(self) -> dict[str, Any]:
        """Backward-compatible shape used by the existing /v1/stac/datasets endpoint."""
        return {
            "dataset_key": self.dataset_key,
            "display_name": self.display_name,
            "priority": self.priority,
            "category": self.category,
            "providers": {
                provider: contract.collection_ids
                for provider, contract in self.providers.items()
                if contract.collection_ids
            },
            "expected_assets": [asset.canonical_name for asset in self.assets],
            "derived_features": self.derived_features,
            "maatitrace_use": self.maatitrace_use,
            "hot_stream_use": self.hot_stream_use,
            "cold_batch_use": self.cold_batch_use,
            "compute_frequency": self.compute_frequency,
            # New optional execution fields. Old callers can ignore these.
            "processor_key": self.processor_key,
            "temporal_type": self.temporal_type,
            "native_resolution_m": self.native_resolution_m,
            "storage_table": self.storage.postgres_table,
            "spatial_level": self.storage.spatial_level,
            "processing_version": self.processing_version,
        }
