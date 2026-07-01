from typing import Any

import requests

from shared.config.settings import settings


class RasterStacClientError(RuntimeError):
    pass


def search_latest_sentinel2_scene(
    provider: str,
    collection_id: str,
    bbox: list[float],
    start_date: str,
    end_date: str,
    max_cloud_cover: float | None,
) -> dict[str, Any]:
    url = f"{settings.stac_catalog_service_url}/v1/stac/search"

    payload = {
        "provider": provider,
        "collection_id": collection_id,
        "bbox": bbox,
        "start_date": start_date,
        "end_date": end_date,
        "max_cloud_cover": max_cloud_cover,
        "limit": 1,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=settings.raster_http_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise RasterStacClientError(
            f"Failed to call STAC catalog service: {exc}"
        ) from exc

    if response.status_code >= 400:
        raise RasterStacClientError(
            f"STAC catalog service returned {response.status_code}: {response.text}"
        )

    data = response.json()
    items = data.get("items") or []

    if not items:
        raise RasterStacClientError(
            "No Sentinel-2 scene found for bbox/date/cloud filters."
        )

    return items[0]