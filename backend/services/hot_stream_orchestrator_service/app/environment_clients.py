from __future__ import annotations

from typing import Any
from uuid import UUID

import requests

from shared.config.settings import settings


class EnvironmentClientError(RuntimeError):
    pass


def _post(url: str, body: dict[str, Any], timeout: int = 600) -> dict[str, Any]:
    try:
        response = requests.post(url, json=body, timeout=timeout)
    except requests.RequestException as exc:
        raise EnvironmentClientError(f"POST failed: {url}: {exc}") from exc
    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}
    if response.status_code >= 400:
        raise EnvironmentClientError(
            f"POST failed: {url}. Status={response.status_code}. Response={payload}"
        )
    return payload


def search_catalog_dataset(
    *,
    dataset_key: str,
    bbox: list[float],
    start_date: str,
    end_date: str,
    limit: int = 10,
    max_cloud_cover: float | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "dataset_key": dataset_key,
        "bbox": bbox,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "max_cloud_cover": max_cloud_cover,
    }
    if provider:
        body["provider"] = provider
    return _post(
        f"{settings.stac_catalog_service_url}/v1/catalog/search",
        body,
        timeout=settings.catalog_http_timeout_seconds + 30,
    )


def process_environment_dataset(
    *,
    dataset_key: str,
    farm_id: UUID | str,
    bbox: list[float],
    farm_polygon_geojson: dict[str, Any],
    h3_resolution: int,
    h3_cells_bigint: list[int],
    source_item: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _post(
        f"{settings.raster_processor_service_url}/v1/raster/process",
        {
            "dataset_key": dataset_key,
            "farm_id": str(farm_id),
            "bbox": bbox,
            "farm_polygon_geojson": farm_polygon_geojson,
            "h3_resolution": h3_resolution,
            "h3_cells_bigint": h3_cells_bigint,
            "source_item": source_item,
            "options": options or {},
        },
        timeout=settings.source_download_timeout_seconds + 300,
    )


def write_environment_to_lakehouse(
    *,
    farm_id: UUID | str,
    process_result: dict[str, Any],
) -> dict[str, Any]:
    body = {
        "farm_id": str(farm_id),
        "dataset_key": process_result["dataset_key"],
        "provider": process_result["provider"],
        "source_collection": process_result.get("source_collection"),
        "source_item_id": process_result["source_item_id"],
        "source_datetime": process_result.get("source_datetime"),
        "processing_version": process_result["processing_version"],
        "spatial_level": process_result["spatial_level"],
        "h3_resolution": process_result.get("h3_resolution"),
        "source_assets_used": process_result.get("source_assets_used", []),
        "records": process_result.get("records", []),
        "metadata": process_result.get("metadata", {}),
    }
    return _post(
        f"{settings.lakehouse_writer_service_url}/v1/lakehouse/environment/write",
        body,
        timeout=600,
    )
