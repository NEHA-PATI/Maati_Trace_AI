from __future__ import annotations

from typing import Any

import numpy as np

from services.raster_processor_service.app.common.h3_generic import aggregate_continuous_h3
from services.raster_processor_service.app.common.raster_io import (
    apply_scale_offset,
    build_target_grid,
    read_asset_to_grid,
    safe_divide,
)
from services.raster_processor_service.app.processors.helpers import find_asset, scale_for_asset


PROCESSING_VERSION = "landsat_c2_l2_zonal_v1"
SR_SCALE = 0.0000275
SR_OFFSET = -0.2
ST_SCALE = 0.00341802
ST_OFFSET = 149.0


def _scale_reflectance(asset: dict[str, Any], raw: np.ndarray) -> np.ndarray:
    scale, offset, nodata = scale_for_asset(
        asset, fallback_scale=SR_SCALE, fallback_offset=SR_OFFSET
    )
    return apply_scale_offset(raw, scale=scale, offset=offset, nodata=nodata)


def _qa_valid(qa_pixel: np.ndarray, qa_radsat: np.ndarray | None) -> np.ndarray:
    finite = np.isfinite(qa_pixel)
    qa = np.nan_to_num(qa_pixel, nan=1).astype("uint16")
    # Collection 2 QA_PIXEL bits: 0 fill, 1 dilated cloud, 2 cirrus,
    # 3 cloud, 4 cloud shadow, 5 snow. Water is not rejected.
    bad_bits = [0, 1, 2, 3, 4, 5]
    invalid = np.zeros(qa.shape, dtype=bool)
    for bit in bad_bits:
        invalid |= ((qa >> bit) & 1).astype(bool)
    if qa_radsat is not None:
        rad = np.nan_to_num(qa_radsat, nan=1).astype("uint16")
        invalid |= rad != 0
    return finite & ~invalid


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    assets = {
        "blue": find_asset(item, "blue", "SR_B2"),
        "green": find_asset(item, "green", "SR_B3"),
        "red": find_asset(item, "red", "SR_B4"),
        "nir": find_asset(item, "nir08", "nir", "SR_B5"),
        "swir16": find_asset(item, "swir16", "SR_B6"),
        "swir22": find_asset(item, "swir22", "SR_B7"),
        "qa_pixel": find_asset(item, "qa_pixel", "QA_PIXEL"),
        "qa_radsat": find_asset(item, "qa_radsat", "QA_RADSAT", required=False),
        "temperature": find_asset(item, "lwir11", "ST_B10", required=False),
    }

    grid = build_target_grid(payload["bbox"], 30.0)
    bands: dict[str, np.ndarray] = {}
    for name in ["blue", "green", "red", "nir", "swir16", "swir22"]:
        raw = read_asset_to_grid(assets[name]["href"], grid, resampling="bilinear")
        bands[name] = _scale_reflectance(assets[name], raw)

    qa_pixel = read_asset_to_grid(assets["qa_pixel"]["href"], grid, resampling="nearest")
    qa_radsat = None
    if assets["qa_radsat"]:
        qa_radsat = read_asset_to_grid(assets["qa_radsat"]["href"], grid, resampling="nearest")

    valid = _qa_valid(qa_pixel, qa_radsat)
    for array in bands.values():
        valid &= np.isfinite(array)

    blue, green, red, nir = bands["blue"], bands["green"], bands["red"], bands["nir"]
    swir16, swir22 = bands["swir16"], bands["swir22"]
    ndvi = safe_divide(nir - red, nir + red)
    ndmi = safe_divide(nir - swir16, nir + swir16)
    msi = safe_divide(swir16, nir)
    bsi = safe_divide((swir16 + red) - (nir + blue), (swir16 + red) + (nir + blue))
    nbr = safe_divide(nir - swir22, nir + swir22)

    arrays = {
        "mean_blue": blue,
        "mean_green": green,
        "mean_red": red,
        "mean_nir": nir,
        "mean_swir16": swir16,
        "mean_swir22": swir22,
        "ndvi": ndvi,
        "ndmi": ndmi,
        "msi": msi,
        "bsi": bsi,
        "nbr": nbr,
    }

    if assets["temperature"]:
        raw_temp = read_asset_to_grid(
            assets["temperature"]["href"], grid, resampling="bilinear"
        )
        scale, offset, nodata = scale_for_asset(
            assets["temperature"],
            fallback_scale=ST_SCALE,
            fallback_offset=ST_OFFSET,
        )
        temp_k = apply_scale_offset(raw_temp, scale=scale, offset=offset, nodata=nodata)
        temp_k[(temp_k < 150) | (temp_k > 400)] = np.nan
        temp_c = temp_k - 273.15
        arrays["surface_temp_k"] = temp_k
        arrays["surface_temp_c"] = temp_c

    rows = aggregate_continuous_h3(
        arrays=arrays,
        valid_mask=valid,
        raster_transform=grid.transform,
        raster_crs=grid.crs,
        h3_cells_bigint=payload["h3_cells_bigint"],
        farm_polygon_geojson=payload["farm_polygon_geojson"],
    )

    props = item.get("properties") or {}
    platform = props.get("platform") or props.get("landsat:platform")
    sensor = props.get("instruments") or props.get("landsat:instrument")
    for row in rows:
        row.update(
            {
                "platform": platform,
                "sensor": sensor if isinstance(sensor, str) else ",".join(sensor or []),
                "scene_cloud_cover": item.get("cloud_cover"),
                "optical_resolution_m": 30,
                "thermal_resolution_m": 100,
            }
        )

    return {
        "dataset_key": "landsat_c2_l2",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "h3",
        "h3_resolution": payload["h3_resolution"],
        "source_assets_used": [name for name, asset in assets.items() if asset],
        "record_count": len(rows),
        "records": rows,
        "metadata": {
            "surface_temperature_source": "Landsat Collection 2 Level-2 thermal product",
            "surface_temperature_is_not_sentinel2_swir": True,
        },
    }
