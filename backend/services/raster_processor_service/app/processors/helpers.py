from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
from shapely.geometry import shape

from services.raster_processor_service.app.common.assets import asset_by_alias


def farm_centroid_lonlat(polygon_geojson: dict[str, Any]) -> tuple[float, float]:
    geom = shape(polygon_geojson)
    centroid = geom.centroid
    return float(centroid.x), float(centroid.y)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def source_date(source_item: dict[str, Any]) -> date:
    dt = parse_iso_datetime(source_item.get("datetime") or source_item.get("start_datetime"))
    return dt.date() if dt else date.today()


def period_8day(source_item: dict[str, Any]) -> tuple[date, date]:
    start = source_date(source_item)
    return start, start + timedelta(days=7)


def scale_for_asset(
    asset: dict[str, Any] | None,
    *,
    fallback_scale: float | None = None,
    fallback_offset: float | None = None,
    fallback_nodata: float | int | None = None,
) -> tuple[float | None, float | None, float | int | None]:
    if asset is None:
        return fallback_scale, fallback_offset, fallback_nodata
    scale = asset.get("scale")
    offset = asset.get("offset")
    nodata = asset.get("nodata")
    return (
        fallback_scale if scale is None else float(scale),
        fallback_offset if offset is None else float(offset),
        fallback_nodata if nodata is None else nodata,
    )


def finite_mean(values: np.ndarray) -> float | None:
    usable = values[np.isfinite(values)]
    if usable.size == 0:
        return None
    return float(np.mean(usable))


def find_asset(source_item: dict[str, Any], *aliases: str, required: bool = True):
    return asset_by_alias(source_item, list(aliases), required=required)
