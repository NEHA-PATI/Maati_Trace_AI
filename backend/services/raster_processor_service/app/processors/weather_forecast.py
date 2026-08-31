from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from shared.config.settings import settings
from services.raster_processor_service.app.processors.helpers import farm_centroid_lonlat


PROCESSING_VERSION = "open_meteo_forecast_v1"
HOURLY = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation",
    "et0_fao_evapotranspiration",
    "vapour_pressure_deficit",
]


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    lon, lat = farm_centroid_lonlat(payload["farm_polygon_geojson"])
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY),
        "forecast_days": int(payload.get("options", {}).get("forecast_days", 7)),
        "timezone": "UTC",
    }
    try:
        response = requests.get(
            settings.open_meteo_forecast_url,
            params=params,
            timeout=settings.catalog_http_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise RuntimeError(f"Open-Meteo forecast request failed: {exc}") from exc

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    issued_at = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    for i, valid_at in enumerate(times):
        def value(name):
            values = hourly.get(name) or []
            return values[i] if i < len(values) else None
        records.append(
            {
                "provider": "open_meteo",
                "model": data.get("model") or "provider_default",
                "issued_at": issued_at,
                "valid_at": valid_at + "+00:00" if valid_at and "+" not in valid_at and not valid_at.endswith("Z") else valid_at,
                "temperature_2m_c": value("temperature_2m"),
                "relative_humidity_2m": value("relative_humidity_2m"),
                "precipitation_mm": value("precipitation"),
                "wind_speed_10m": value("wind_speed_10m"),
                "wind_direction_10m": value("wind_direction_10m"),
                "shortwave_radiation": value("shortwave_radiation"),
                "et0_mm": value("et0_fao_evapotranspiration"),
                "vapour_pressure_deficit": value("vapour_pressure_deficit"),
                "source_resolution_m": None,
                "aggregation_method": "farm_centroid_forecast",
            }
        )

    return {
        "dataset_key": "weather_forecast",
        "provider": item["provider"],
        "source_collection": None,
        "source_item_id": item["item_id"],
        "source_datetime": issued_at,
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "farm",
        "h3_resolution": None,
        "source_assets_used": HOURLY,
        "record_count": len(records),
        "records": records,
        "metadata": {
            "latitude": lat,
            "longitude": lon,
            "timezone": "UTC",
        },
    }
