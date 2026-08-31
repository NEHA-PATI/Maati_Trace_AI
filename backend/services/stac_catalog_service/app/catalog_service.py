from __future__ import annotations

from typing import Any

from services.stac_catalog_service.app.collection_registry import get_dataset_contract
from services.stac_catalog_service.app.source_adapters.cmr import search_cmr_dataset
from services.stac_catalog_service.app.source_adapters.stac import search_stac_dataset
from services.stac_catalog_service.app.source_adapters.virtual import build_virtual_item


class CatalogDispatchError(RuntimeError):
    pass


def _ordered_providers(dataset) -> list[tuple[str, Any]]:
    rows = [
        (name, contract)
        for name, contract in dataset.providers.items()
        if contract.enabled
    ]
    return sorted(rows, key=lambda row: row[1].priority)


def search_dataset(
    *,
    dataset_key: str,
    bbox: list[float],
    start_date: str,
    end_date: str,
    limit: int = 10,
    max_cloud_cover: float | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    dataset = get_dataset_contract(dataset_key)
    if dataset is None:
        raise CatalogDispatchError(f"Unknown dataset_key: {dataset_key}")

    candidates = _ordered_providers(dataset)
    if provider:
        candidates = [row for row in candidates if row[0] == provider]
        if not candidates:
            raise CatalogDispatchError(
                f"Dataset {dataset.dataset_key} is not configured for provider {provider}"
            )

    errors: list[str] = []

    for provider_name, provider_contract in candidates:
        try:
            adapter = provider_contract.source_adapter
            if adapter == "stac":
                for collection_id in provider_contract.collection_ids:
                    effective_start = start_date
                    effective_end = end_date
                    if dataset.temporal_type in {"static", "annual"}:
                        # Static/annual context should not disappear merely because a
                        # hot-stream request uses a recent temporal window.
                        effective_start = "1900-01-01"
                        effective_end = end_date
                    items = search_stac_dataset(
                        dataset_key=dataset.dataset_key,
                        provider=provider_name,
                        collection_id=collection_id,
                        bbox=bbox,
                        start_date=effective_start,
                        end_date=effective_end,
                        limit=limit,
                        max_cloud_cover=(max_cloud_cover if dataset.category in {"optical_satellite", "optical_thermal_satellite"} else None),
                    )
                    if items:
                        return {
                            "dataset_key": dataset.dataset_key,
                            "provider": provider_name,
                            "acquisition_method": "stac",
                            "returned_count": len(items),
                            "items": items,
                        }
            elif adapter == "cmr":
                if not provider_contract.short_name:
                    raise CatalogDispatchError(
                        f"CMR provider for {dataset.dataset_key} is missing short_name"
                    )
                items = search_cmr_dataset(
                    dataset_key=dataset.dataset_key,
                    provider=provider_name,
                    short_name=provider_contract.short_name,
                    version=provider_contract.version,
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
                if items:
                    return {
                        "dataset_key": dataset.dataset_key,
                        "provider": provider_name,
                        "acquisition_method": "cmr",
                        "returned_count": len(items),
                        "items": items,
                    }
            elif adapter in {"cds", "wcs", "json_api"}:
                collection_id = (
                    provider_contract.collection_ids[0]
                    if provider_contract.collection_ids
                    else provider_contract.short_name
                )
                item = build_virtual_item(
                    dataset_key=dataset.dataset_key,
                    provider=provider_name,
                    acquisition_method=adapter,
                    collection_id=collection_id,
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    properties={
                        "provider_metadata": provider_contract.metadata,
                        "variables": dataset.variables,
                    },
                )
                return {
                    "dataset_key": dataset.dataset_key,
                    "provider": provider_name,
                    "acquisition_method": adapter,
                    "returned_count": 1,
                    "items": [item],
                }
            else:
                raise CatalogDispatchError(
                    f"Unsupported source adapter: {adapter}"
                )
        except Exception as exc:
            errors.append(f"{provider_name}: {exc}")
            continue

    # No provider returned data. This is not the same as an invalid registry.
    return {
        "dataset_key": dataset.dataset_key,
        "provider": provider or (candidates[0][0] if candidates else "unknown"),
        "acquisition_method": "unknown",
        "returned_count": 0,
        "items": [],
        "errors": errors,
    }
