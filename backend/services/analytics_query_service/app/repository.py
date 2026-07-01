from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class AnalyticsQueryRepositoryError(RuntimeError):
    pass


FEATURE_COLUMNS = """
    feature_id,
    farm_id,
    farmer_id,
    fpo_id,

    state_name,
    district_name,
    district_code,
    block_name,
    block_code,

    snapshot_date,
    scene_id,
    scene_datetime,
    scene_cloud_cover,

    h3_resolution,
    h3_index,

    pixel_count,
    valid_pixel_count,
    cloud_pixel_count,
    nodata_pixel_count,
    cloud_percentage,

    mean_blue,
    mean_green,
    mean_red,
    mean_rededge1,
    mean_rededge2,
    mean_rededge3,
    mean_nir,
    mean_nir08,
    mean_swir16,
    mean_swir22,

    ndvi,
    gndvi,
    evi,
    savi,
    ndmi,
    ndwi,
    mndwi,
    msi,
    bsi,
    nbr,
    nbr2,
    ndre,
    reci,

    source_assets_used,
    parquet_uri,
    created_at
"""


def get_latest_snapshot_key(farm_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT snapshot_date, scene_id
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        ORDER BY snapshot_date DESC, created_at DESC
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()

    return dict(row) if row else None


def get_features_for_snapshot(
    farm_id: UUID | str,
    snapshot_date: Any,
    scene_id: str,
) -> list[dict[str, Any]]:
    query = text(
        f"""
        SELECT {FEATURE_COLUMNS}
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND snapshot_date = :snapshot_date
          AND scene_id = :scene_id
        ORDER BY h3_index;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "snapshot_date": snapshot_date,
                    "scene_id": scene_id,
                },
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to read Sentinel-2 features: {exc}"
        ) from exc

    return [dict(row) for row in rows]


def get_latest_features(farm_id: UUID | str) -> list[dict[str, Any]]:
    latest = get_latest_snapshot_key(farm_id)

    if latest is None:
        return []

    return get_features_for_snapshot(
        farm_id=farm_id,
        snapshot_date=latest["snapshot_date"],
        scene_id=latest["scene_id"],
    )


def get_history(farm_id: UUID | str, limit: int = 20) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            farm_id,
            snapshot_date,
            scene_id,
            MAX(scene_datetime) AS scene_datetime,
            MAX(scene_cloud_cover) AS scene_cloud_cover,

            COUNT(*) AS row_count,
            COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
            COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
            COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,

            ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,

            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi

        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        GROUP BY farm_id, snapshot_date, scene_id
        ORDER BY snapshot_date DESC
        LIMIT :limit;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "limit": limit,
                },
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to read Sentinel-2 history: {exc}"
        ) from exc

    return [dict(row) for row in rows]


def get_latest_aggregate(farm_id: UUID | str) -> dict[str, Any] | None:
    latest = get_latest_snapshot_key(farm_id)

    if latest is None:
        return None

    query = text(
        """
        SELECT
            farm_id,
            MIN(farmer_id::text)::uuid AS farmer_id,
            MIN(fpo_id::text)::uuid AS fpo_id,

            MAX(district_name) AS district_name,
            MAX(block_name) AS block_name,
            MAX(block_code) AS block_code,

            snapshot_date,
            scene_id,
            MAX(scene_datetime) AS scene_datetime,
            MAX(scene_cloud_cover) AS scene_cloud_cover,

            COUNT(*) AS row_count,
            COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
            COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
            COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,

            ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,

            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(gndvi)::numeric, 6)::double precision AS avg_gndvi,
            ROUND(AVG(evi)::numeric, 6)::double precision AS avg_evi,
            ROUND(AVG(savi)::numeric, 6)::double precision AS avg_savi,

            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(mndwi)::numeric, 6)::double precision AS avg_mndwi,
            ROUND(AVG(msi)::numeric, 6)::double precision AS avg_msi,

            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi,
            ROUND(AVG(nbr)::numeric, 6)::double precision AS avg_nbr,
            ROUND(AVG(nbr2)::numeric, 6)::double precision AS avg_nbr2,

            ROUND(AVG(ndre)::numeric, 6)::double precision AS avg_ndre,
            ROUND(AVG(reci)::numeric, 6)::double precision AS avg_reci

        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND snapshot_date = :snapshot_date
          AND scene_id = :scene_id
        GROUP BY farm_id, snapshot_date, scene_id;
        """
    )

    try:
        with engine.connect() as conn:
            row = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "snapshot_date": latest["snapshot_date"],
                    "scene_id": latest["scene_id"],
                },
            ).mappings().first()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to read latest aggregate: {exc}"
        ) from exc

    return dict(row) if row else None


def get_farm_trends(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            farm_id,
            snapshot_date,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi,
            ROUND(AVG(evi)::numeric, 6)::double precision AS avg_evi,
            ROUND(AVG(savi)::numeric, 6)::double precision AS avg_savi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(msi)::numeric, 6)::double precision AS avg_msi,
            ROUND(AVG(nbr)::numeric, 6)::double precision AS avg_nbr,
            ROUND(AVG(ndre)::numeric, 6)::double precision AS avg_ndre
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        GROUP BY farm_id, snapshot_date
        ORDER BY snapshot_date DESC
        LIMIT 30;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_farm_h3_cells(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        f"""
        SELECT {FEATURE_COLUMNS}
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
          )
        ORDER BY h3_index;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_farm_grid_cells(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            grid_cell_id,
            farm_id,
            grid_size_meters,
            grid_row,
            grid_col,
            cell_polygon_geojson,
            cell_centroid_lon,
            cell_centroid_lat,
            coverage_ratio,
            created_at
        FROM farm_grid_cells
        WHERE farm_id = :farm_id
        ORDER BY grid_row, grid_col;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_latest_grid_values(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            gv.*,
            gc.grid_row,
            gc.grid_col,
            gc.cell_polygon_geojson,
            gc.cell_centroid_lon,
            gc.cell_centroid_lat
        FROM farm_grid_daily_values gv
        JOIN farm_grid_cells gc ON gc.grid_cell_id = gv.grid_cell_id
        WHERE gv.farm_id = :farm_id
          AND gv.snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM farm_grid_daily_values
            WHERE farm_id = :farm_id
          )
        ORDER BY gc.grid_row, gc.grid_col;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_grid_value_history(farm_id: UUID | str, limit: int = 10) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            snapshot_date,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi
        FROM farm_grid_daily_values
        WHERE farm_id = :farm_id
        GROUP BY snapshot_date
        ORDER BY snapshot_date DESC
        LIMIT :limit;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id), "limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def get_farmer_analytics_summary(farmer_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            :farmer_id::uuid AS farmer_id,
            COUNT(DISTINCT farm_id) AS farm_count,
            COUNT(*) AS h3_record_count,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi
        FROM h3_sentinel2_features
        WHERE farmer_id = :farmer_id;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().first()
    return dict(row) if row else {"farmer_id": str(farmer_id), "farm_count": 0, "h3_record_count": 0}


def get_fpo_analytics_summary(fpo_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            :fpo_id::uuid AS fpo_id,
            COUNT(DISTINCT farm_id) AS farm_count,
            COUNT(*) AS h3_record_count,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi
        FROM h3_sentinel2_features
        WHERE fpo_id = :fpo_id;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().first()
    return dict(row) if row else {"fpo_id": str(fpo_id), "farm_count": 0, "h3_record_count": 0}
