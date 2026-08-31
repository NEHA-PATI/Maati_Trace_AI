from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NormalizedAsset(BaseModel):
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


class NormalizedSourceItem(BaseModel):
    dataset_key: str
    provider: str
    acquisition_method: str
    item_id: str
    collection_id: str | None = None
    product_id: str | None = None
    datetime: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    bbox: list[float] | None = None
    cloud_cover: float | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    assets: list[NormalizedAsset] = Field(default_factory=list)
