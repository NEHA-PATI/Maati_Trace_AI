from __future__ import annotations

import os
from typing import Any

import h5py
import numpy as np

from services.raster_processor_service.app.common.assets import first_data_asset
from services.raster_processor_service.app.common.download import download_to_temp


PROCESSING_VERSION = "smap_l4_v8_farm_v1"


def _find_dataset_paths(handle: h5py.File) -> dict[str, str]:
    found: dict[str, str] = {}
    targets = {
        "sm_surface": ["sm_surface"],
        "sm_rootzone": ["sm_rootzone"],
        "cell_lat": ["cell_lat", "latitude", "lat"],
        "cell_lon": ["cell_lon", "longitude", "lon"],
    }

    def visitor(name: str, obj):
        if not isinstance(obj, h5py.Dataset):
            return
        leaf = name.split("/")[-1].lower()
        for canonical, aliases in targets.items():
            if canonical in found:
                continue
            if leaf in aliases:
                found[canonical] = name

    handle.visititems(visitor)
    return found


def _masked_values(dataset: h5py.Dataset) -> np.ndarray:
    values = np.asarray(dataset[...], dtype="float64")
    fill = dataset.attrs.get("_FillValue")
    missing = dataset.attrs.get("missing_value")
    if fill is not None:
        values[np.isclose(values, float(np.asarray(fill).reshape(-1)[0]))] = np.nan
    if missing is not None:
        values[np.isclose(values, float(np.asarray(missing).reshape(-1)[0]))] = np.nan
    return values


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    asset = first_data_asset(item)
    path = download_to_temp(asset["href"], requires_earthdata=True)
    try:
        with h5py.File(path, "r") as handle:
            paths = _find_dataset_paths(handle)
            missing = [name for name in ["sm_surface", "sm_rootzone", "cell_lat", "cell_lon"] if name not in paths]
            if missing:
                raise RuntimeError(f"SMAP HDF5 missing expected arrays: {missing}")
            surface = _masked_values(handle[paths["sm_surface"]])
            rootzone = _masked_values(handle[paths["sm_rootzone"]])
            lat = _masked_values(handle[paths["cell_lat"]])
            lon = _masked_values(handle[paths["cell_lon"]])

            if lat.shape != surface.shape or lon.shape != surface.shape:
                # Some files expose 1-D coordinate axes. Broadcast where possible.
                if lat.ndim == 1 and lon.ndim == 1 and surface.ndim == 2:
                    lon, lat = np.meshgrid(lon, lat)
                else:
                    raise RuntimeError(
                        f"SMAP coordinate shape mismatch: surface={surface.shape}, lat={lat.shape}, lon={lon.shape}"
                    )

            west, south, east, north = payload["bbox"]
            within = (
                np.isfinite(lat) & np.isfinite(lon)
                & (lat >= south) & (lat <= north)
                & (lon >= west) & (lon <= east)
            )
            # For farms smaller than 9 km, bbox may contain no grid-cell centre.
            # Use the nearest SMAP cell to farm centre instead of claiming fine resolution.
            if not np.any(within):
                center_lat = (south + north) / 2.0
                center_lon = (west + east) / 2.0
                dist2 = (lat - center_lat) ** 2 + (lon - center_lon) ** 2
                flat_index = int(np.nanargmin(dist2))
                within = np.zeros(surface.shape, dtype=bool)
                within.reshape(-1)[flat_index] = True

            s = surface[within]
            r = rootzone[within]
            s = s[np.isfinite(s)]
            r = r[np.isfinite(r)]
            surface_mean = float(np.mean(s)) if s.size else None
            rootzone_mean = float(np.mean(r)) if r.size else None

        record = {
            "observed_at": item.get("datetime") or item.get("start_datetime"),
            "surface_soil_moisture": surface_mean,
            "root_zone_soil_moisture": rootzone_mean,
            "source_dataset": "SPL4SMGP",
            "source_version": (item.get("properties") or {}).get("version_id") or "8",
            "source_resolution_m": 9000.0,
            "aggregation_method": "farm_bbox_mean_or_nearest_9km_cell",
            "source_granule_id": item["item_id"],
        }
    finally:
        try: os.remove(path)
        except OSError: pass

    return {
        "dataset_key": "smap_l4_sm",
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
        "metadata": {"resolution_warning": "SMAP L4 is 9 km context, not field-scale measurement."},
    }
