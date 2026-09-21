from __future__ import annotations

import os
from typing import Any

import numpy as np
import xarray as xr

from services.raster_processor_service.app.common.assets import first_data_asset
from services.raster_processor_service.app.common.download import download_to_temp
from services.raster_processor_service.app.processors.helpers import source_date


PROCESSING_VERSION = "gpm_imerg_daily_v1"


def _open_gpm(path: str):
    errors: list[str] = []
    for group in [None, "Grid"]:
        try:
            kwargs = {"group": group} if group else {}
            ds = xr.open_dataset(path, **kwargs)
            if any(name in ds.variables for name in ["precipitation", "precipitationCal"]):
                return ds
            ds.close()
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("Could not open IMERG precipitation variable: " + " | ".join(errors))


def _subset_mean(ds, bbox: list[float]) -> tuple[float | None, str | None]:
    var_name = "precipitation" if "precipitation" in ds.variables else "precipitationCal"
    da = ds[var_name]
    west, south, east, north = bbox

    lat_name = next((name for name in ["lat", "latitude"] if name in ds.coords or name in ds.variables), None)
    lon_name = next((name for name in ["lon", "longitude"] if name in ds.coords or name in ds.variables), None)
    if lat_name is None or lon_name is None:
        raise RuntimeError("IMERG file does not expose latitude/longitude coordinates")

    lat = ds[lat_name]
    lon = ds[lon_name]

    # For tiny farms, direct slice-based selection can return an EMPTY subset
    # (no grid point falls inside the farm's bbox on IMERG's ~0.1 deg / ~10 km
    # grid). xarray's slice-based .sel() does not raise in that case - it just
    # returns a zero-length array - so an except-only fallback never triggers
    # and the farm silently ends up with no data. Explicitly check size here
    # and fall back to the nearest whole grid cell to the farm centre.
    subset = None
    try:
        lat_slice = slice(south, north) if float(lat[0]) <= float(lat[-1]) else slice(north, south)
        lon_slice = slice(west, east) if float(lon[0]) <= float(lon[-1]) else slice(east, west)
        candidate = da.sel({lat_name: lat_slice, lon_name: lon_slice})
        if candidate.size > 0:
            subset = candidate
    except Exception:
        subset = None

    if subset is None:
        subset = da.sel(
            {
                lat_name: (south + north) / 2.0,
                lon_name: (west + east) / 2.0,
            },
            method="nearest",
        )

    values = np.asarray(subset.values, dtype="float64")
    values[~np.isfinite(values)] = np.nan
    values[values < 0] = np.nan
    usable = values[np.isfinite(values)]
    mean_value = float(np.mean(usable)) if usable.size else None
    unit = da.attrs.get("units")
    return mean_value, unit


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    asset = first_data_asset(item)
    path = download_to_temp(asset["href"], requires_earthdata=True)
    try:
        ds = _open_gpm(path)
        try:
            rainfall, unit = _subset_mean(ds, payload["bbox"])
        finally:
            ds.close()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

    # GPM_3IMERGDE V07 daily precipitation is mm/day. If a provider returns
    # a different unit, persist it in metadata and do not silently convert.
    record = {
        "observation_date": source_date(item).isoformat(),
        "source_dataset": "gpm_imerg",
        "source_product_version": (item.get("properties") or {}).get("version_id") or "07",
        "precipitation_mm": rainfall if unit in {None, "mm/day", "mm / day", "mm"} else None,
        "source_resolution_m": 10000.0,
        "aggregation_method": "farm_bbox_mean_or_nearest_coarse_grid_cell",
        "source_item_ids": [item["item_id"]],
        "source_unit": unit,
    }

    return {
        "dataset_key": "gpm_imerg",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime") or item.get("start_datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "farm",
        "h3_resolution": None,
        "source_assets_used": [asset.get("key") or "data"],
        "record_count": 1,
        "records": [record],
        "metadata": {"resolution_warning": "IMERG is coarse regional rainfall context, not an on-farm rain gauge."},
    }
