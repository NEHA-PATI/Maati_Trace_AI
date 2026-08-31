from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text

from shared.db.postgres import engine


STATIC_TABLES = {
    "cop_dem_glo30": "h3_terrain_features",
    "esa_worldcover": "h3_landcover_features",
    "jrc_surface_water": "h3_surface_water_features",
    "soilgrids_v2": "h3_soilgrids_features",
}


def expected_static_rows(
    dataset_key: str,
    h3_count: int,
    options: dict[str, Any] | None = None,
) -> int:
    if dataset_key != "soilgrids_v2":
        return h3_count
    options = options or {}
    properties = options.get("properties") or [
        "phh2o", "soc", "nitrogen", "clay", "sand", "silt", "bdod", "cec", "cfvo"
    ]
    depths = options.get("depths_cm") or [
        [0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]
    ]
    return h3_count * len(properties) * len(depths)


def static_dataset_is_cached(
    farm_id: UUID | str,
    dataset_key: str,
    expected_rows: int,
) -> bool:
    table = STATIC_TABLES.get(dataset_key)
    if not table:
        return False
    query = text(f"SELECT COUNT(*) FROM {table} WHERE farm_id = :farm_id")
    with engine.connect() as conn:
        count = int(conn.execute(query, {"farm_id": str(farm_id)}).scalar() or 0)
    return count >= expected_rows
