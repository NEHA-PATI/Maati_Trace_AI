from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine
from services.analytics_query_service.app.repository import (
    AnalyticsQueryRepositoryError,
)


class H3TemporalRepositoryError(AnalyticsQueryRepositoryError):
    pass


def get_latest_valid_h3_mosaic(
    farm_id: UUID | str,
) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT *
        FROM h3_latest_valid_observations_v1
        WHERE farm_id = :farm_id
        ORDER BY h3_index;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {"farm_id": str(farm_id)},
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise H3TemporalRepositoryError(
            f"Failed to read the H3 temporal mosaic: {exc}"
        ) from exc

    return [dict(row) for row in rows]


def get_valid_h3_history(
    farm_id: UUID | str,
    h3_index: int,
    limit: int = 20,
) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            h3_index,
            snapshot_date,
            scene_id,
            scene_datetime,
            valid_area_m2,
            observed_area_m2,
            valid_fraction,
            ndvi,
            ndmi,
            bsi,
            fvc_proxy,
            nirv,
            water_area_m2,
            processing_version
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND h3_index = :h3_index
          AND processing_version LIKE 's2_zonal_v%'
          AND COALESCE(observed_area_m2, 0) > 0
          AND COALESCE(valid_area_m2, 0) > 0
          AND COALESCE(valid_fraction, 0) >= 0.20
          AND ndvi IS NOT NULL
        ORDER BY
            snapshot_date DESC,
            scene_datetime DESC NULLS LAST,
            created_at DESC
        LIMIT :limit;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "h3_index": int(h3_index),
                    "limit": int(limit),
                },
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise H3TemporalRepositoryError(
            f"Failed to read H3 observation history: {exc}"
        ) from exc

    return [dict(row) for row in rows]