from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EnvironmentLakehouseWriteRequest(BaseModel):
    farm_id: UUID
    dataset_key: str
    provider: str
    source_collection: str | None = None
    source_item_id: str
    source_datetime: str | None = None
    processing_version: str
    spatial_level: str
    h3_resolution: int | None = None
    source_assets_used: list[str] = Field(default_factory=list)
    records: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnvironmentLakehouseWriteResponse(BaseModel):
    dataset_key: str
    postgres_table: str
    farm_id: UUID
    row_count: int
    postgres_rows_written: int
    parquet_rows_written: int
    storage_mode: str
    parquet_uris: list[str]
