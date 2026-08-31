from __future__ import annotations

from typing import Any

import numpy as np

from services.raster_processor_service.app.common.h3_generic import aggregate_continuous_h3
from services.raster_processor_service.app.common.raster_io import build_target_grid, read_asset_to_grid
from services.raster_processor_service.app.processors.helpers import find_asset


PROCESSING_VERSION = "cop_dem_glo30_zonal_v1"


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    asset = find_asset(item, "data", "elevation", "dem")
    grid = build_target_grid(payload["bbox"], 30.0)
    elevation = read_asset_to_grid(asset["href"], grid, resampling="bilinear")
    valid = np.isfinite(elevation) & (elevation > -500) & (elevation < 9000)

    fill = elevation.copy()
    if np.any(valid):
        fill[~valid] = float(np.nanmedian(elevation[valid]))
    else:
        fill[:] = 0.0

    res = float(grid.resolution_m)
    dz_dy, dz_dx = np.gradient(fill, res, res)
    slope = np.degrees(np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2)))
    aspect = (90.0 - np.degrees(np.arctan2(dz_dy, -dz_dx))) % 360.0
    slope[~valid] = np.nan
    aspect[~valid] = np.nan

    rows = aggregate_continuous_h3(
        arrays={"elevation_m": elevation, "slope_deg": slope, "aspect_deg": aspect},
        valid_mask=valid,
        raster_transform=grid.transform,
        raster_crs=grid.crs,
        h3_cells_bigint=payload["h3_cells_bigint"],
        farm_polygon_geojson=payload["farm_polygon_geojson"],
        reducers={
            "elevation_m": ["mean", "min", "max"],
            "slope_deg": ["mean", "max"],
            "aspect_deg": ["mean"],
        },
    )

    for row in rows:
        if "aspect_deg" in row:
            row["mean_aspect_deg"] = row.pop("aspect_deg")
        row["source_dataset"] = "cop_dem_glo30"
        row["source_version"] = item.get("collection_id") or "cop-dem-glo-30"
        row["native_resolution_m"] = 30.0

    return {
        "dataset_key": "cop_dem_glo30",
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
        "metadata": {"product_type": "DSM"},
    }
