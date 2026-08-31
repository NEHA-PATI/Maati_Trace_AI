from __future__ import annotations

from typing import Any


def build_virtual_item(
    *,
    dataset_key: str,
    provider: str,
    acquisition_method: str,
    collection_id: str | None,
    bbox: list[float],
    start_date: str,
    end_date: str,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dataset_key": dataset_key,
        "provider": provider,
        "acquisition_method": acquisition_method,
        "collection_id": collection_id,
        "product_id": collection_id,
        "item_id": f"{dataset_key}:{start_date}:{end_date}",
        "scene_id": f"{dataset_key}:{start_date}:{end_date}",
        "datetime": None,
        "start_datetime": f"{start_date}T00:00:00Z",
        "end_datetime": f"{end_date}T23:59:59Z",
        "bbox": bbox,
        "cloud_cover": None,
        "properties": properties or {},
        "assets": [],
    }
