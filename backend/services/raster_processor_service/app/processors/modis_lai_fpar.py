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
    period_8day,
    scale_for_asset,
)


PROCESSING_VERSION = "mod15a2h_v061_farm_v1"

# +/- pixels around the farm centroid to search for a QC-valid pixel, at the
# product's native 500 m grid. A farm much smaller than one MODIS pixel can
# sit exactly on a masked (cloud/QC-bad) pixel while a genuinely good pixel is
# only a few hundred metres away; a single warped destination pixel anchored
# at the farm's own bbox has no way to see that neighbour. See
# common/raster_io.py::sample_native_window for the full rationale.
SEARCH_HALF_WINDOW_PIXELS = 3


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
    lai_asset = find_asset(item, "Lai_500m", "lai")
    fpar_asset = find_asset(item, "Fpar_500m", "fpar")
    lai_sd_asset = find_asset(item, "LaiStdDev_500m", required=False)
    fpar_sd_asset = find_asset(item, "FparStdDev_500m", required=False)
    qc_asset = find_asset(item, "FparLai_QC", required=False)

    lon, lat = farm_centroid_lonlat(payload["farm_polygon_geojson"])

    lai_sample = sample_native_window(lai_asset["href"], lon, lat, half_window_pixels=SEARCH_HALF_WINDOW_PIXELS)
    fpar_sample = sample_native_window(fpar_asset["href"], lon, lat, half_window_pixels=SEARCH_HALF_WINDOW_PIXELS)
    if lai_sample is None or fpar_sample is None:
        raise ValueError("Farm centroid falls outside the MODIS LAI/FPAR source tile")

    lai_scale, lai_offset, _ = scale_for_asset(lai_asset, fallback_scale=0.1, fallback_offset=0.0)
    fpar_scale, fpar_offset, _ = scale_for_asset(fpar_asset, fallback_scale=0.01, fallback_offset=0.0)

    # MOD15A2H documented valid raw range is 0-100 (fill/flag codes are >100).
    valid_mask = (
        np.isfinite(lai_sample.values) & (lai_sample.values >= 0) & (lai_sample.values <= 100)
        & np.isfinite(fpar_sample.values) & (fpar_sample.values >= 0) & (fpar_sample.values <= 100)
    )

    qc_sample = None
    if qc_asset:
        qc_sample = sample_native_window(qc_asset["href"], lon, lat, half_window_pixels=SEARCH_HALF_WINDOW_PIXELS)
        if qc_sample is not None and qc_sample.values.shape == valid_mask.shape:
            qc_u8 = np.nan_to_num(qc_sample.values, nan=255).astype("uint8")
            # MODLAND_QC bit 0: 0 = good quality.
            valid_mask &= (qc_u8 & 1) == 0

    raw_lai, row_offset, col_offset = nearest_valid_pixel(lai_sample, valid_mask)
    raw_fpar = None
    if row_offset is not None:
        # LAI and FPAR come from the same MODIS tile/grid, so the same pixel
        # position that was valid for LAI is used for FPAR directly.
        target_row = fpar_sample.center_row + row_offset
        target_col = fpar_sample.center_col + col_offset
        if 0 <= target_row < fpar_sample.values.shape[0] and 0 <= target_col < fpar_sample.values.shape[1]:
            candidate = fpar_sample.values[target_row, target_col]
            raw_fpar = float(candidate) if np.isfinite(candidate) else None

    def optional_stddev(asset, fallback_scale) -> float | None:
        if not asset or row_offset is None:
            return None
        sample = sample_native_window(asset["href"], lon, lat, half_window_pixels=SEARCH_HALF_WINDOW_PIXELS)
        if sample is None:
            return None
        target_row = sample.center_row + row_offset
        target_col = sample.center_col + col_offset
        if not (0 <= target_row < sample.values.shape[0] and 0 <= target_col < sample.values.shape[1]):
            return None
        raw = sample.values[target_row, target_col]
        if not np.isfinite(raw):
            return None
        scale, offset, _ = scale_for_asset(asset, fallback_scale=fallback_scale, fallback_offset=0.0)
        return _apply_scale(float(raw), scale, offset)

    found = row_offset is not None
    fallback_used = found and (row_offset != 0 or col_offset != 0)
    aggregation_method = "farm_centroid_nearest_valid_pixel"
    if fallback_used:
        aggregation_method += f"_offset_row{row_offset}_col{col_offset}"

    start, end = period_8day(item)
    record = {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "lai": _apply_scale(raw_lai, lai_scale, lai_offset),
        "fpar": _apply_scale(raw_fpar, fpar_scale, fpar_offset),
        "lai_stddev": optional_stddev(lai_sd_asset, 0.1),
        "fpar_stddev": optional_stddev(fpar_sd_asset, 0.01),
        "valid_fraction": 1.0 if found else 0.0,
        "source_product": "MOD15A2H",
        "source_version": "061",
        "native_resolution_m": 500.0,
        "aggregation_method": aggregation_method,
    }
    used = [a["key"] for a in [lai_asset, fpar_asset, lai_sd_asset, fpar_sd_asset, qc_asset] if a]
    return {
        "dataset_key": "modis_lai_fpar",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "farm",
        "h3_resolution": None,
        "source_assets_used": used,
        "record_count": 1,
        "records": [record],
        "metadata": {
            "composite_period_days": 8,
            "search_radius_pixels": SEARCH_HALF_WINDOW_PIXELS,
            "search_radius_m": SEARCH_HALF_WINDOW_PIXELS * 500,
            "nearest_valid_pixel_used": fallback_used,
        },
    }
