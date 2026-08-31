from __future__ import annotations

from typing import Any

import numpy as np

from services.raster_processor_service.app.common.raster_io import (
    nearest_valid_pixel,
    sample_native_window,
)
from services.raster_processor_service.app.processors.helpers import (
    farm_centroid_lonlat,
    find_asset,
    scale_for_asset,
)


PROCESSING_VERSION = "mod16a3gf_v061_farm_v1"

# See modis_lai_fpar.py for the full rationale: a farm smaller than one 500 m
# MODIS pixel needs a small real-neighbourhood search, not a single warped
# destination pixel, or it silently loses valid data sitting a few hundred
# metres away.
SEARCH_HALF_WINDOW_PIXELS = 3

# MOD16 documented special/fill codes on the raw (unscaled) ET/PET band:
# 32761 water body, 32762 urban/built-up, 32763 permanent snow/ice,
# 32764 permanent wetland, 32765 permanent cropland, 32766 barren,
# 32767 fill/no data. Any raw value at or above this floor is not a real
# ET/PET measurement.
SPECIAL_CODE_FLOOR = 32761


def _apply_scale(raw: float | None, scale: float | None, offset: float | None) -> float | None:
    if raw is None:
        return None
    value = raw
    if scale is not None:
        value *= scale
    if offset is not None:
        value += offset
    return value


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    et_asset = find_asset(item, "ET_500m")
    pet_asset = find_asset(item, "PET_500m")
    le_asset = find_asset(item, "LE_500m", required=False)
    ple_asset = find_asset(item, "PLE_500m", required=False)
    qc_asset = find_asset(item, "ET_QC_500m", required=False)

    lon, lat = farm_centroid_lonlat(payload["farm_polygon_geojson"])

    et_sample = sample_native_window(et_asset["href"], lon, lat, half_window_pixels=SEARCH_HALF_WINDOW_PIXELS)
    if et_sample is None:
        raise ValueError("Farm centroid falls outside the MODIS ET source tile")

    valid_mask = (
        np.isfinite(et_sample.values)
        & (et_sample.values >= 0)
        & (et_sample.values < SPECIAL_CODE_FLOOR)
    )

    raw_et, row_offset, col_offset = nearest_valid_pixel(et_sample, valid_mask)

    def value_at_offset(asset: dict[str, Any] | None, fallback_scale: float) -> float | None:
        if not asset or row_offset is None:
            return None
        sample = sample_native_window(asset["href"], lon, lat, half_window_pixels=SEARCH_HALF_WINDOW_PIXELS)
        if sample is None:
            return None
        row = sample.center_row + row_offset
        col = sample.center_col + col_offset
        if not (0 <= row < sample.values.shape[0] and 0 <= col < sample.values.shape[1]):
            return None
        raw = sample.values[row, col]
        if not np.isfinite(raw) or raw < 0 or raw >= SPECIAL_CODE_FLOOR:
            return None
        scale, offset, _ = scale_for_asset(asset, fallback_scale=fallback_scale, fallback_offset=0.0)
        return _apply_scale(float(raw), scale, offset)

    et_scale, et_offset, _ = scale_for_asset(et_asset, fallback_scale=0.1, fallback_offset=0.0)
    found = row_offset is not None
    fallback_used = found and (row_offset != 0 or col_offset != 0)
    aggregation_method = "farm_centroid_nearest_valid_pixel"
    if fallback_used:
        aggregation_method += f"_offset_row{row_offset}_col{col_offset}"

    # STAC items normalized by stac_client.py only carry a single top-level
    # `datetime`, which pystac leaves as None for date-range items (annual
    # composites like this one use start_datetime/end_datetime instead,
    # nested under `properties` per the STAC spec).
    properties = item.get("properties") or {}
    period_start = (
        item.get("start_datetime") or properties.get("start_datetime") or item.get("datetime") or ""
    )[:10]
    period_end = (
        item.get("end_datetime") or properties.get("end_datetime") or ""
    )[:10] or period_start

    record = {
        "period_start": period_start,
        "period_end": period_end,
        # 1 kg/m^2 water depth == 1 mm of water.
        "et_mm": _apply_scale(raw_et, et_scale, et_offset),
        "pet_mm": value_at_offset(pet_asset, 0.1),
        "latent_heat_j_m2_day": value_at_offset(le_asset, 10000.0),
        "potential_latent_heat_j_m2_day": value_at_offset(ple_asset, 10000.0),
        "valid_fraction": 1.0 if found else 0.0,
        "source_product": "MOD16A3GF",
        "source_version": "061",
        "native_resolution_m": 500.0,
        "aggregation_method": aggregation_method,
    }
    used = [a["key"] for a in [et_asset, pet_asset, le_asset, ple_asset, qc_asset] if a]
    return {
        "dataset_key": "modis_et",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime") or item.get("start_datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "farm",
        "h3_resolution": None,
        "source_assets_used": used,
        "record_count": 1,
        "records": [record],
        "metadata": {
            "temporal_aggregation": "annual_gap_filled",
            "source_change_note": (
                "Switched from MOD16A2 (8-day, HDF4 via NASA CMR) to "
                "MOD16A3GF (annual, gap-filled, COG via Planetary Computer). "
                "No 8-day COG-converted MOD16A2 product exists, and the "
                "installed GDAL build has no HDF4 driver, so the raw CMR "
                "HDF4 granules could not be opened at all. period_start / "
                "period_end reflect the full calendar year this record "
                "covers, not an 8-day window."
            ),
            "search_radius_pixels": SEARCH_HALF_WINDOW_PIXELS,
            "search_radius_m": SEARCH_HALF_WINDOW_PIXELS * 500,
            "nearest_valid_pixel_used": fallback_used,
        },
    }
