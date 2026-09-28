from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Iterable


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def content_hash(value: Any) -> str:
    payload = json.dumps(value, default=_json_default, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_item_hash(item: dict[str, Any]) -> str:
    """Hash stable STAC identity fields, excluding signed asset URLs."""
    properties = item.get("properties") or {}
    stable = {
        "id": item.get("id") or item.get("item_id") or item.get("source_item_id"),
        "collection": item.get("collection") or item.get("collection_id"),
        "datetime": item.get("datetime") or item.get("start_datetime") or item.get("end_datetime"),
        "start_datetime": item.get("start_datetime") or properties.get("start_datetime"),
        "end_datetime": item.get("end_datetime") or properties.get("end_datetime"),
        "version": item.get("version") or properties.get("version") or properties.get("version_id"),
    }
    return content_hash(stable)


def h3_index_set_hash(h3_indexes: Iterable[int]) -> str:
    return content_hash([int(value) for value in sorted(set(h3_indexes))])


def materialization_fingerprint(
    *,
    farm_id: str,
    boundary_hash: str,
    h3_resolution: int,
    h3_indexes: Iterable[int],
    dataset_key: str,
    dataset_version: str | None,
    source_version: str | None,
    processing_version: str | None,
    materialization_version: str = "1",
) -> str:
    return content_hash({
        "farm_id": str(farm_id),
        "boundary_hash": boundary_hash,
        "h3_resolution": int(h3_resolution),
        "h3_index_set_hash": h3_index_set_hash(h3_indexes),
        "dataset_key": dataset_key,
        "dataset_version": dataset_version,
        "source_version": source_version,
        "processing_version": processing_version,
        "materialization_version": materialization_version,
    })
