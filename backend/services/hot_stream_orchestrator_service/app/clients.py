from __future__ import annotations

from typing import Any
from uuid import UUID

import requests

from shared.config.settings import settings


class OrchestratorClientError(RuntimeError):
    pass


def _get_json(url: str, timeout: int = 60) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise OrchestratorClientError(f"GET failed: {url}. Error: {exc}") from exc

    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}

    if response.status_code >= 400:
        raise OrchestratorClientError(
            f"GET failed: {url}. Status={response.status_code}. Response={payload}"
        )

    return payload


def _post_json(url: str, body: dict[str, Any], timeout: int = 240) -> dict[str, Any]:
    try:
        response = requests.post(url, json=body, timeout=timeout)
    except requests.RequestException as exc:
        raise OrchestratorClientError(f"POST failed: {url}. Error: {exc}") from exc

    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}

    if response.status_code >= 400:
        raise OrchestratorClientError(
            f"POST failed: {url}. Status={response.status_code}. Response={payload}"
        )

    return payload


def get_farm(farm_id: UUID | str) -> dict[str, Any]:
    url = f"{settings.farm_registry_service_url}/v1/farms/{farm_id}"
    return _get_json(url, timeout=60)


def run_raster_preview_from_search(
    farm_id: UUID | str,
    bbox: list[float],
    provider: str,
    collection_id: str,
    start_date: str,
    end_date: str,
    max_cloud_cover: float | None,
    h3_resolution: int,
    h3_cells_bigint: list[int] | None = None,
) -> dict[str, Any]:
    url = (
        f"{settings.raster_processor_service_url}"
        "/v1/raster/sentinel2/indices/preview-from-search"
    )

    body = {
        "farm_id": str(farm_id),
        "bbox": bbox,
        "h3_resolution": h3_resolution,
        "provider": provider,
        "collection_id": collection_id,
        "start_date": start_date,
        "end_date": end_date,
        "max_cloud_cover": max_cloud_cover,
    }

    if h3_cells_bigint is not None:
        body["h3_cells_bigint"] = h3_cells_bigint

    return _post_json(url, body, timeout=300)


def write_sentinel2_to_lakehouse(
    farm_id: UUID | str,
    raster_result: dict[str, Any],
) -> dict[str, Any]:
    url = (
        f"{settings.lakehouse_writer_service_url}"
        "/v1/lakehouse/sentinel2/write"
    )

    body = {
        "farm_id": str(farm_id),
        "scene_id": raster_result["scene_id"],
        "scene_datetime": raster_result.get("scene_datetime"),
        "scene_cloud_cover": raster_result.get("scene_cloud_cover"),
        "h3_resolution": raster_result["h3_resolution"],
        "source_assets_used": raster_result.get("source_assets_used", []),
        "features": raster_result.get("features", []),
    }

    return _post_json(url, body, timeout=300)
