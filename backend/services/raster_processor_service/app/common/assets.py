from __future__ import annotations

from typing import Any


def asset_by_alias(
    source_item: dict[str, Any],
    aliases: list[str],
    *,
    required: bool = True,
) -> dict[str, Any] | None:
    assets = source_item.get("assets") or []
    aliases_lower = {str(alias).lower() for alias in aliases}
    for asset in assets:
        key = str(asset.get("key") or "").lower()
        common = str(asset.get("common_name") or "").lower()
        title = str(asset.get("title") or "").lower()
        if key in aliases_lower or common in aliases_lower or any(alias in title for alias in aliases_lower):
            return asset
    if required:
        raise ValueError(
            f"Required asset not found. Expected one of: {', '.join(aliases)}"
        )
    return None


def first_data_asset(source_item: dict[str, Any]) -> dict[str, Any]:
    assets = source_item.get("assets") or []
    if not assets:
        raise ValueError("Source item has no downloadable data assets")
    for asset in assets:
        roles = asset.get("roles") or []
        if "data" in roles and asset.get("href"):
            return asset
    for asset in assets:
        if asset.get("href"):
            return asset
    raise ValueError("Source item contains no asset href")
