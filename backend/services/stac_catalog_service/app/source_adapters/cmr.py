from __future__ import annotations

from typing import Any

import requests

from shared.config.settings import settings


class CmrAdapterError(RuntimeError):
    pass


def _pick_data_links(entry: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for link in entry.get("links") or []:
        href = str(link.get("href") or "").strip()
        if not href:
            continue
        if link.get("inherited") is True:
            continue
        rel = str(link.get("rel") or "")
        title = str(link.get("title") or "")
        if rel and "data" not in rel and "enclosure" not in rel:
            continue
        # Prefer actual science files, not browse/documentation links.
        lower = (href + " " + title).lower()
        if any(token in lower for token in ["browse", "documentation", "metadata.xml", "opendap"]):
            continue
        output.append(
            {
                "key": f"data_{len(output) + 1}",
                "href": href,
                "title": title or None,
                "media_type": link.get("type"),
                "roles": ["data"],
                "common_name": None,
                "metadata": {"rel": rel},
            }
        )
    return output


def search_cmr_dataset(
    *,
    dataset_key: str,
    provider: str,
    short_name: str,
    version: str | None,
    bbox: list[float],
    start_date: str,
    end_date: str,
    limit: int,
) -> list[dict[str, Any]]:
    west, south, east, north = bbox
    params: dict[str, Any] = {
        "short_name": short_name,
        "bounding_box": f"{west},{south},{east},{north}",
        "temporal": f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
        "page_size": min(limit, 200),
        "sort_key[]": "-start_date",
    }
    if version:
        params["version"] = version

    headers = {"Accept": "application/json"}
    token = getattr(settings, "earthdata_token", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            settings.nasa_cmr_granules_url,
            params=params,
            headers=headers,
            timeout=settings.catalog_http_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        entries = ((payload.get("feed") or {}).get("entry") or [])[:limit]

        # DAACs do not format version strings uniformly (e.g. 8 vs 008).
        # If a version-qualified search yields nothing, retry by short_name and
        # persist the returned version_id rather than silently inventing one.
        if not entries and version:
            retry_params = dict(params)
            retry_params.pop("version", None)
            response = requests.get(
                settings.nasa_cmr_granules_url,
                params=retry_params,
                headers=headers,
                timeout=settings.catalog_http_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            entries = ((payload.get("feed") or {}).get("entry") or [])[:limit]
    except Exception as exc:
        raise CmrAdapterError(f"CMR granule search failed for {short_name}: {exc}") from exc
    rows: list[dict[str, Any]] = []

    for entry in entries:
        item_id = str(entry.get("id") or entry.get("producer_granule_id") or "").strip()
        start_time = entry.get("time_start")
        end_time = entry.get("time_end")
        assets = _pick_data_links(entry)
        rows.append(
            {
                "dataset_key": dataset_key,
                "provider": provider,
                "acquisition_method": "cmr",
                "collection_id": short_name,
                "product_id": entry.get("producer_granule_id"),
                "item_id": item_id,
                "scene_id": item_id,
                "datetime": start_time,
                "start_datetime": start_time,
                "end_datetime": end_time,
                "bbox": bbox,
                "cloud_cover": None,
                "properties": {
                    "version_id": entry.get("version_id"),
                    "producer_granule_id": entry.get("producer_granule_id"),
                },
                "assets": assets,
            }
        )
    return rows
