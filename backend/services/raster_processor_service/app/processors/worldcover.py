from __future__ import annotations

from typing import Any

import numpy as np

from services.raster_processor_service.app.common.h3_generic import aggregate_categorical_h3
from services.raster_processor_service.app.common.raster_io import build_target_grid, read_asset_to_grid
from services.raster_processor_service.app.processors.helpers import find_asset


PROCESSING_VERSION = "worldcover_zonal_v1"
CLASS_CODES = {
    10: "tree_cover_fraction",
    20: "shrubland_fraction",
    30: "grassland_fraction",
    40: "cropland_fraction",
    50: "built_fraction",
    60: "bare_sparse_fraction",
    70: "snow_ice_fraction",
    80: "permanent_water_fraction",
    90: "herbaceous_wetland_fraction",
    95: "mangrove_fraction",
    100: "moss_lichen_fraction",
}


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    asset = find_asset(item, "map", "classification", "data")
    grid = build_target_grid(payload["bbox"], 10.0)
    raw = read_asset_to_grid(asset["href"], grid, resampling="nearest")
    valid = np.isfinite(raw) & np.isin(raw.astype("int32"), list(CLASS_CODES))
    classes = np.nan_to_num(raw, nan=-9999).astype("int32")

    rows = aggregate_categorical_h3(
        class_array=classes,
        valid_mask=valid,
        raster_transform=grid.transform,
        raster_crs=grid.crs,
        h3_cells_bigint=payload["h3_cells_bigint"],
        farm_polygon_geojson=payload["farm_polygon_geojson"],
        class_codes=CLASS_CODES,
    )
    props = item.get("properties") or {}
    reference_year = props.get("start_datetime") or props.get("datetime") or item.get("datetime")
    if isinstance(reference_year, str) and len(reference_year) >= 4:
        try:
            reference_year = int(reference_year[:4])
        except Exception:
            reference_year = None
    else:
        reference_year = props.get("year")
    if reference_year is None:
        import re
        match = re.search(r"(?:19|20)\d{2}", str(item.get("item_id") or ""))
        reference_year = int(match.group(0)) if match else 0
    for row in rows:
        row["reference_year"] = reference_year
        row["source_dataset"] = "esa_worldcover"
        row["source_version"] = item.get("collection_id")
        row["native_resolution_m"] = 10.0

    return {
        "dataset_key": "esa_worldcover",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "h3",
        "h3_resolution": payload["h3_resolution"],
        "source_assets_used": [asset["key"]],
        "record_count": len(rows),
        "records": rows,
        "metadata": {},
    }
