from __future__ import annotations

from typing import Any

from services.stac_catalog_service.app.stac_client import search_items


def search_stac_dataset(
    *,
    dataset_key: str,
    provider: str,
    collection_id: str,
    bbox: list[float],
    start_date: str,
    end_date: str,
    limit: int,
    max_cloud_cover: float | None,
) -> list[dict[str, Any]]:
    rows = search_items(
        provider=provider,
        collection_id=collection_id,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        limit=limit,
    )
    for row in rows:
        row["dataset_key"] = dataset_key
        row["acquisition_method"] = "stac"
        row["item_id"] = row.get("scene_id")
    return rows
