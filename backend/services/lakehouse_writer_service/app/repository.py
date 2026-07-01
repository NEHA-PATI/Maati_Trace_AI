from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class LakehouseRepositoryError(RuntimeError):
    pass


def get_farm_context(farm_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            farm_id,
            farmer_id,
            fpo_id,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            h3_resolution,
            is_active
        FROM farms
        WHERE farm_id = :farm_id
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()

    if row is None:
        raise LakehouseRepositoryError(f"Farm not found: {farm_id}")

    if not row["is_active"]:
        raise LakehouseRepositoryError(f"Farm is inactive: {farm_id}")

    return dict(row)


def upsert_sentinel2_feature_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    query = text(
        """
        INSERT INTO h3_sentinel2_features (
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
            parquet_uri
        )
        VALUES (
            :farm_id,
            :farmer_id,
            :fpo_id,
            :state_name,
            :district_name,
            :district_code,
            :block_name,
            :block_code,

            :snapshot_date,
            :scene_id,
            :scene_datetime,
            :scene_cloud_cover,

            :h3_resolution,
            :h3_index,

            :pixel_count,
            :valid_pixel_count,
            :cloud_pixel_count,
            :nodata_pixel_count,
            :cloud_percentage,

            :mean_blue,
            :mean_green,
            :mean_red,
            :mean_rededge1,
            :mean_rededge2,
            :mean_rededge3,
            :mean_nir,
            :mean_nir08,
            :mean_swir16,
            :mean_swir22,

            :ndvi,
            :gndvi,
            :evi,
            :savi,
            :ndmi,
            :ndwi,
            :mndwi,
            :msi,
            :bsi,
            :nbr,
            :nbr2,
            :ndre,
            :reci,

            :source_assets_used,
            :parquet_uri
        )
        ON CONFLICT (farm_id, snapshot_date, scene_id, h3_index)
        DO UPDATE SET
            farmer_id = EXCLUDED.farmer_id,
            fpo_id = EXCLUDED.fpo_id,
            state_name = EXCLUDED.state_name,
            district_name = EXCLUDED.district_name,
            district_code = EXCLUDED.district_code,
            block_name = EXCLUDED.block_name,
            block_code = EXCLUDED.block_code,

            scene_datetime = EXCLUDED.scene_datetime,
            scene_cloud_cover = EXCLUDED.scene_cloud_cover,

            h3_resolution = EXCLUDED.h3_resolution,

            pixel_count = EXCLUDED.pixel_count,
            valid_pixel_count = EXCLUDED.valid_pixel_count,
            cloud_pixel_count = EXCLUDED.cloud_pixel_count,
            nodata_pixel_count = EXCLUDED.nodata_pixel_count,
            cloud_percentage = EXCLUDED.cloud_percentage,

            mean_blue = EXCLUDED.mean_blue,
            mean_green = EXCLUDED.mean_green,
            mean_red = EXCLUDED.mean_red,
            mean_rededge1 = EXCLUDED.mean_rededge1,
            mean_rededge2 = EXCLUDED.mean_rededge2,
            mean_rededge3 = EXCLUDED.mean_rededge3,
            mean_nir = EXCLUDED.mean_nir,
            mean_nir08 = EXCLUDED.mean_nir08,
            mean_swir16 = EXCLUDED.mean_swir16,
            mean_swir22 = EXCLUDED.mean_swir22,

            ndvi = EXCLUDED.ndvi,
            gndvi = EXCLUDED.gndvi,
            evi = EXCLUDED.evi,
            savi = EXCLUDED.savi,
            ndmi = EXCLUDED.ndmi,
            ndwi = EXCLUDED.ndwi,
            mndwi = EXCLUDED.mndwi,
            msi = EXCLUDED.msi,
            bsi = EXCLUDED.bsi,
            nbr = EXCLUDED.nbr,
            nbr2 = EXCLUDED.nbr2,
            ndre = EXCLUDED.ndre,
            reci = EXCLUDED.reci,

            source_assets_used = EXCLUDED.source_assets_used,
            parquet_uri = EXCLUDED.parquet_uri,
            updated_at = now();
        """
    )

    try:
        with engine.begin() as conn:
            for row in rows:
                conn.execute(query, row)
    except SQLAlchemyError as exc:
        raise LakehouseRepositoryError(
            f"Failed to write Sentinel-2 feature rows: {exc}"
        ) from exc

    return len(rows)