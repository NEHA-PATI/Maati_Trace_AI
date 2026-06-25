from typing import Any

import planetary_computer
from pystac import Collection
from pystac_client import Client
from pystac_client.exceptions import APIError

from services.stac_catalog_service.app.providers import get_provider_url


class StacCatalogError(RuntimeError):
    pass


def open_client(provider: str) -> Client:
    url = get_provider_url(provider)

    try:
        return Client.open(url)
    except Exception as exc:
        raise StacCatalogError(f"Failed to open STAC provider {provider}: {exc}") from exc


def should_sign_assets(provider: str) -> bool:
    return provider.strip().lower() == "planetary_computer"


def safe_collection_to_dict(collection: Collection) -> dict[str, Any]:
    return {
        "id": collection.id,
        "title": collection.title,
        "description": collection.description,
        "license": collection.license,
        "extent": collection.extent.to_dict() if collection.extent else None,
        "summaries": collection.summaries.to_dict() if collection.summaries else {},
    }


def list_provider_collections(provider: str) -> list[dict[str, Any]]:
    client = open_client(provider)

    try:
        collections = list(client.get_collections())
    except Exception as exc:
        raise StacCatalogError(f"Failed to list provider collections: {exc}") from exc

    return [safe_collection_to_dict(collection) for collection in collections]


def get_collection_details(
    provider: str,
    collection_id: str,
) -> dict[str, Any]:
    client = open_client(provider)

    try:
        collection = client.get_collection(collection_id)
    except Exception as exc:
        raise StacCatalogError(
            f"Failed to get collection {collection_id} from {provider}: {exc}"
        ) from exc

    if collection is None:
        raise StacCatalogError(
            f"Collection not found: {collection_id} on provider {provider}"
        )

    return safe_collection_to_dict(collection)


def extract_asset_summary_keys(collection_details: dict[str, Any]) -> list[str]:
    summaries = collection_details.get("summaries") or {}

    if "assets" in summaries and isinstance(summaries["assets"], dict):
        return sorted(list(summaries["assets"].keys()))

    if "eo:bands" in summaries:
        bands = summaries.get("eo:bands") or []
        keys = []
        for band in bands:
            if isinstance(band, dict):
                name = band.get("name") or band.get("common_name")
                if name:
                    keys.append(str(name))
        return sorted(set(keys))

    return []


def normalize_asset(
    key: str,
    asset: Any,
    provider: str,
) -> dict[str, Any]:
    href = asset.href

    if should_sign_assets(provider):
        href = planetary_computer.sign(href)

    extra_fields = asset.extra_fields or {}

    common_name = None
    center_wavelength = None
    full_width_half_max = None

    bands = extra_fields.get("eo:bands")
    if isinstance(bands, list) and bands:
        first_band = bands[0]
        if isinstance(first_band, dict):
            common_name = first_band.get("common_name") or first_band.get("name")
            center_wavelength = first_band.get("center_wavelength")
            full_width_half_max = first_band.get("full_width_half_max")

    return {
        "key": key,
        "href": href,
        "title": asset.title,
        "media_type": asset.media_type,
        "roles": asset.roles or [],
        "common_name": common_name,
        "center_wavelength": center_wavelength,
        "full_width_half_max": full_width_half_max,
    }


def normalize_item(
    item: Any,
    provider: str,
    collection_id: str,
) -> dict[str, Any]:
    properties = dict(item.properties or {})

    cloud_cover = (
        properties.get("eo:cloud_cover")
        or properties.get("s2:cloud_cover")
        or properties.get("landsat:cloud_cover")
    )

    assets = [
        normalize_asset(key=key, asset=asset, provider=provider)
        for key, asset in item.assets.items()
    ]

    return {
        "provider": provider,
        "collection_id": collection_id,
        "scene_id": item.id,
        "datetime": item.datetime.isoformat() if item.datetime else None,
        "bbox": item.bbox,
        "cloud_cover": cloud_cover,
        "properties": properties,
        "assets": assets,
    }


def build_query(max_cloud_cover: float | None) -> dict[str, Any] | None:
    if max_cloud_cover is None:
        return None

    return {
        "eo:cloud_cover": {
            "lt": max_cloud_cover,
        }
    }


def search_items(
    provider: str,
    collection_id: str,
    bbox: list[float],
    start_date: str,
    end_date: str,
    max_cloud_cover: float | None,
    limit: int,
) -> list[dict[str, Any]]:
    client = open_client(provider)

    query = build_query(max_cloud_cover)

    try:
        search = client.search(
            collections=[collection_id],
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query=query,
            limit=limit,
        )
        items = list(search.items())
    except APIError as exc:
        raise StacCatalogError(f"STAC search failed: {exc}") from exc
    except Exception as exc:
        raise StacCatalogError(f"STAC search failed: {exc}") from exc

    normalized_items = [
        normalize_item(
            item=item,
            provider=provider,
            collection_id=collection_id,
        )
        for item in items[:limit]
    ]

    normalized_items.sort(
        key=lambda row: row.get("datetime") or "",
        reverse=True,
    )

    return normalized_items