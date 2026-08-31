from __future__ import annotations

from typing import Any

import xarray as xr


class XarrayIOError(RuntimeError):
    pass


def open_netcdf(path_or_url: str, *, group: str | None = None, engine: str | None = None) -> xr.Dataset:
    kwargs: dict[str, Any] = {}
    if group:
        kwargs["group"] = group
    if engine:
        kwargs["engine"] = engine
    try:
        return xr.open_dataset(path_or_url, **kwargs)
    except Exception as exc:
        raise XarrayIOError(f"Failed to open NetCDF/HDF-backed dataset: {exc}") from exc


def open_zarr(store: str, *, consolidated: bool | None = None, storage_options: dict[str, Any] | None = None) -> xr.Dataset:
    kwargs: dict[str, Any] = {"storage_options": storage_options or {}}
    if consolidated is not None:
        kwargs["consolidated"] = consolidated
    try:
        return xr.open_zarr(store, **kwargs)
    except Exception as exc:
        raise XarrayIOError(f"Failed to open Zarr store: {exc}") from exc
