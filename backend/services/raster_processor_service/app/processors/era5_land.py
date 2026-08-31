from __future__ import annotations

import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import cdsapi
import numpy as np
import xarray as xr

from shared.config.settings import settings


PROCESSING_VERSION = "era5_land_daily_v1"
DATASET_ID = "reanalysis-era5-land"
VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "skin_temperature",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "volumetric_soil_water_layer_4",
]


def _date_range(start: str, end: str) -> list[date]:
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    if last < first:
        raise ValueError("end_date is before start_date")
    days = []
    cursor = first
    while cursor <= last:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _group_days(days: list[date]):
    grouped: dict[tuple[int, int], list[int]] = defaultdict(list)
    for day in days:
        grouped[(day.year, day.month)].append(day.day)
    return grouped


def _open_cds_file(path: str) -> xr.Dataset:
    try:
        return xr.open_dataset(path)
    except Exception:
        # New CDS downloads can occasionally be zip containers despite a NetCDF request.
        import zipfile
        if zipfile.is_zipfile(path):
            extract_dir = tempfile.mkdtemp(prefix="maatitrace_era5_")
            with zipfile.ZipFile(path) as zf:
                zf.extractall(extract_dir)
            nc_files = []
            for root, _, files in os.walk(extract_dir):
                for name in files:
                    if name.lower().endswith((".nc", ".netcdf")):
                        nc_files.append(os.path.join(root, name))
            if not nc_files:
                raise RuntimeError("CDS returned a zip without a NetCDF file")
            return xr.open_mfdataset(nc_files, combine="by_coords")
        raise


def _coord_name(ds: xr.Dataset, candidates: list[str]) -> str:
    for name in candidates:
        if name in ds.coords or name in ds.variables:
            return name
    raise RuntimeError(f"Missing coordinate; expected one of {candidates}")


def _spatial_mean(da: xr.DataArray) -> xr.DataArray:
    dims = [dim for dim in da.dims if dim.lower() in {"latitude", "lat", "longitude", "lon"}]
    return da.mean(dim=dims, skipna=True) if dims else da


def _find_variable(ds: xr.Dataset, aliases: list[str]) -> xr.DataArray | None:
    for alias in aliases:
        if alias in ds.data_vars:
            return ds[alias]
    # CDS often uses short names.
    lowered = {name.lower(): name for name in ds.data_vars}
    for alias in aliases:
        if alias.lower() in lowered:
            return ds[lowered[alias.lower()]]
    return None


def process(payload: dict[str, Any]) -> dict[str, Any]:
    if not settings.cds_api_key.strip():
        raise RuntimeError("CDS_API_KEY is required for ERA5-Land")
    item = payload["source_item"]
    start = (item.get("start_datetime") or "")[:10]
    end = (item.get("end_datetime") or "")[:10]
    days = _date_range(start, end)
    if len(days) > settings.era5_max_days_per_request:
        raise RuntimeError(
            f"ERA5-Land request is limited to {settings.era5_max_days_per_request} days per materialization"
        )

    north = payload["bbox"][3]
    west = payload["bbox"][0]
    south = payload["bbox"][1]
    east = payload["bbox"][2]
    client = cdsapi.Client(url=settings.cds_api_url, key=settings.cds_api_key, quiet=True)

    datasets: list[xr.Dataset] = []
    temp_paths: list[str] = []
    try:
        for (year, month), month_days in _group_days(days).items():
            fd, path = tempfile.mkstemp(prefix="maatitrace_era5_", suffix=".nc")
            os.close(fd)
            temp_paths.append(path)
            request = {
                "variable": VARIABLES,
                "year": str(year),
                "month": f"{month:02d}",
                "day": [f"{d:02d}" for d in sorted(set(month_days))],
                "time": [f"{hour:02d}:00" for hour in range(24)],
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": [north, west, south, east],
            }
            client.retrieve(DATASET_ID, request, path)
            datasets.append(_open_cds_file(path))

        ds = xr.combine_by_coords(datasets) if len(datasets) > 1 else datasets[0]
        time_name = _coord_name(ds, ["valid_time", "time"])
        time_values = np.asarray(ds[time_name].values)

        t2m = _find_variable(ds, ["t2m", "2m_temperature"])
        d2m = _find_variable(ds, ["d2m", "2m_dewpoint_temperature"])
        skt = _find_variable(ds, ["skt", "skin_temperature"])
        swvl1 = _find_variable(ds, ["swvl1", "volumetric_soil_water_layer_1"])
        swvl2 = _find_variable(ds, ["swvl2", "volumetric_soil_water_layer_2"])
        swvl3 = _find_variable(ds, ["swvl3", "volumetric_soil_water_layer_3"])
        swvl4 = _find_variable(ds, ["swvl4", "volumetric_soil_water_layer_4"])

        def series(da):
            if da is None:
                return None
            return np.asarray(_spatial_mean(da).values, dtype="float64").reshape(-1)

        values = {
            "t2m": series(t2m), "d2m": series(d2m), "skt": series(skt),
            "swvl1": series(swvl1), "swvl2": series(swvl2),
            "swvl3": series(swvl3), "swvl4": series(swvl4),
        }
        date_keys = np.array([str(np.datetime64(t, "D")) for t in time_values])
        records: list[dict[str, Any]] = []
        for day in days:
            key = day.isoformat()
            mask = date_keys == key
            if not np.any(mask):
                continue

            def agg(name: str, reducer: str = "mean", kelvin: bool = False):
                arr = values[name]
                if arr is None:
                    return None
                selected = arr[mask]
                selected = selected[np.isfinite(selected)]
                if selected.size == 0:
                    return None
                if reducer == "min": value = float(np.min(selected))
                elif reducer == "max": value = float(np.max(selected))
                else: value = float(np.mean(selected))
                if kelvin:
                    value -= 273.15
                return value

            records.append(
                {
                    "observation_date": key,
                    "dataset_key": "era5_land",
                    "temperature_mean_c": agg("t2m", kelvin=True),
                    "temperature_min_c": agg("t2m", "min", kelvin=True),
                    "temperature_max_c": agg("t2m", "max", kelvin=True),
                    "dewpoint_mean_c": agg("d2m", kelvin=True),
                    "skin_temperature_mean_c": agg("skt", kelvin=True),
                    "soil_water_0_7": agg("swvl1"),
                    "soil_water_7_28": agg("swvl2"),
                    "soil_water_28_100": agg("swvl3"),
                    "soil_water_100_289": agg("swvl4"),
                    "source_resolution_m": 9000.0,
                    "aggregation_method": "hourly_spatial_mean_then_daily_statistics",
                    "source_version": "ERA5-Land",
                }
            )

        return {
            "dataset_key": "era5_land",
            "provider": item["provider"],
            "source_collection": DATASET_ID,
            "source_item_id": item["item_id"],
            "source_datetime": item.get("start_datetime"),
            "processing_version": PROCESSING_VERSION,
            "spatial_level": "farm",
            "h3_resolution": None,
            "source_assets_used": VARIABLES,
            "record_count": len(records),
            "records": records,
            "metadata": {
                "v1_scope": "temperature, dewpoint, skin temperature and soil-water layers; accumulated rainfall/flux fields intentionally excluded",
            },
        }
    finally:
        for ds in datasets:
            try:
                ds.close()
            except Exception:
                pass
        for path in temp_paths:
            try:
                os.remove(path)
            except OSError:
                pass
