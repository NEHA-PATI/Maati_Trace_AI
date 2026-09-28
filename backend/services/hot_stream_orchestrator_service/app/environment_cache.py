from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

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
    *,
    expected_h3_indexes: list[int] | None = None,
    expected_fingerprint: str | None = None,
) -> bool:
    table = STATIC_TABLES.get(dataset_key)
    if not table:
        return False
    try:
        with engine.connect() as conn:
            count = int(conn.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE farm_id = :farm_id"),
                {"farm_id": str(farm_id)},
            ).scalar() or 0)
            if count < expected_rows:
                return False

            if expected_h3_indexes is not None:
                rows = conn.execute(
                    text(f"SELECT DISTINCT h3_index FROM {table} WHERE farm_id = :farm_id"),
                    {"farm_id": str(farm_id)},
                ).scalars().all()
                if {int(value) for value in rows} != {int(value) for value in expected_h3_indexes}:
                    return False

            if expected_fingerprint:
                materialized = conn.execute(
                    text(
                        """
                        SELECT materialization_fingerprint
                        FROM farm_dataset_materializations
                        WHERE farm_id = :farm_id AND dataset_key = :dataset_key
                        """
                    ),
                    {"farm_id": str(farm_id), "dataset_key": dataset_key},
                ).scalar()
                if materialized != expected_fingerprint:
                    return False
    except SQLAlchemyError:
        # A missing stabilization migration must never turn an unverified
        # cache into a valid cache.
        return False
    return True
