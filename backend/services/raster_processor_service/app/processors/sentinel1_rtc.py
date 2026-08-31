from __future__ import annotations

from typing import Any

import numpy as np

from services.raster_processor_service.app.common.h3_generic import aggregate_continuous_h3
from services.raster_processor_service.app.common.raster_io import (
    build_target_grid,
    read_asset_to_grid,
    safe_divide,
)
from services.raster_processor_service.app.processors.helpers import find_asset


PROCESSING_VERSION = "s1_rtc_zonal_v1"


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    vv_asset = find_asset(item, "vv", "VV", required=False)
    vh_asset = find_asset(item, "vh", "VH", required=False)
    if vv_asset is None or vh_asset is None:
        raise ValueError("Sentinel-1 RTC V1 requires both VV and VH assets")

    grid = build_target_grid(payload["bbox"], 10.0)
    vv = read_asset_to_grid(vv_asset["href"], grid, resampling="bilinear")
    vh = read_asset_to_grid(vh_asset["href"], grid, resampling="bilinear")

    # Planetary Computer Sentinel-1 RTC gamma0 assets are linear power values.
    valid = np.isfinite(vv) & np.isfinite(vh) & (vv > 0) & (vh > 0)
    vv_db = np.full(vv.shape, np.nan, dtype="float64")
    vh_db = np.full(vh.shape, np.nan, dtype="float64")
    vv_db[valid] = 10.0 * np.log10(vv[valid])
    vh_db[valid] = 10.0 * np.log10(vh[valid])
    ratio = safe_divide(vh, vv)
    rvi = safe_divide(4.0 * vh, vv + vh)

    rows = aggregate_continuous_h3(
        arrays={
            "mean_vv": vv,
            "mean_vh": vh,
            "mean_vv_db": vv_db,
            "mean_vh_db": vh_db,
            "vh_vv_ratio": ratio,
            "rvi": rvi,
        },
        valid_mask=valid,
        raster_transform=grid.transform,
        raster_crs=grid.crs,
        h3_cells_bigint=payload["h3_cells_bigint"],
        farm_polygon_geojson=payload["farm_polygon_geojson"],
    )

    props = item.get("properties") or {}
    orbit_direction = (
        props.get("sat:orbit_state")
        or props.get("s1:orbit_state")
        or props.get("orbit_state")
    )
    relative_orbit = (
        props.get("sat:relative_orbit")
        or props.get("s1:relative_orbit")
        or props.get("relative_orbit")
    )
    for row in rows:
        row.update(
            {
                "orbit_direction": orbit_direction,
                "relative_orbit": relative_orbit,
                "native_resolution_m": 10.0,
            }
        )

    return {
        "dataset_key": "sentinel_1_rtc",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "h3",
        "h3_resolution": payload["h3_resolution"],
        "source_assets_used": ["vv", "vh"],
        "record_count": len(rows),
        "records": rows,
        "metadata": {"backscatter_unit": "linear_gamma0_and_derived_db"},
    }
