from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceAsset(BaseModel):
    key: str
    href: str | None = None
    title: str | None = None
    media_type: str | None = None
    roles: list[str] = Field(default_factory=list)
    common_name: str | None = None
    unit: str | None = None
    scale: float | None = None
    offset: float | None = None
    nodata: float | int | None = None
    spatial_resolution_m: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceItem(BaseModel):
    dataset_key: str
    provider: str
    acquisition_method: str
    item_id: str
    collection_id: str | None = None
    product_id: str | None = None
    scene_id: str | None = None
    datetime: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    bbox: list[float] | None = None
    cloud_cover: float | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    assets: list[SourceAsset] = Field(default_factory=list)


class DatasetProcessRequest(BaseModel):
    dataset_key: str
    farm_id: str
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    farm_polygon_geojson: dict[str, Any]
    h3_resolution: int = Field(default=12, ge=7, le=12)
    h3_cells_bigint: list[int] = Field(default_factory=list)
    source_item: SourceItem
    options: dict[str, Any] = Field(default_factory=dict)


class DatasetProcessResponse(BaseModel):
    dataset_key: str
    provider: str
    source_collection: str | None = None
    source_item_id: str
    source_datetime: str | None = None
    processing_version: str
    spatial_level: Literal["h3", "farm"]
    h3_resolution: int | None = None
    source_assets_used: list[str] = Field(default_factory=list)
    record_count: int
    records: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)
