BEGIN;

-- One fast lookup path for each H3 cell's historical observations.
CREATE INDEX IF NOT EXISTS idx_h3_s2_farm_cell_observation_desc
ON h3_sentinel2_features (
    farm_id,
    h3_index,
    snapshot_date DESC,
    scene_datetime DESC,
    created_at DESC
)
WHERE processing_version LIKE 's2_zonal_v%';

-- Version 1 uses 20% valid farm-clipped area as the minimum needed to
-- describe an individual H3 cell. This is intentionally a cell-level gate.
CREATE OR REPLACE VIEW h3_latest_valid_observations_v1 AS
WITH valid_history AS (
    SELECT
        feature_id,
        farm_id,
        farmer_id,
        fpo_id,
        state_name,
        district_name,
        district_code,
        block_name,
        block_code,
        h3_resolution,
        h3_index,
        snapshot_date,
        scene_id,
        scene_datetime,
        scene_cloud_cover,
        observed_area_m2,
        valid_area_m2,
        cloud_area_m2,
        shadow_area_m2,
        water_area_m2,
        snow_area_m2,
        nodata_area_m2,
        invalid_area_m2,
        valid_fraction,
        cloud_percentage,
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
        fvc_proxy,
        nirv,
        processing_version,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY farm_id, h3_index
            ORDER BY
                snapshot_date DESC,
                scene_datetime DESC NULLS LAST,
                created_at DESC
        ) AS observation_rank
    FROM h3_sentinel2_features
    WHERE processing_version LIKE 's2_zonal_v%'
      AND COALESCE(observed_area_m2, 0) > 0
      AND COALESCE(valid_area_m2, 0) > 0
      AND COALESCE(valid_fraction, 0) >= 0.20
      AND ndvi IS NOT NULL
),
latest AS (
    SELECT *
    FROM valid_history
    WHERE observation_rank = 1
),
previous AS (
    SELECT *
    FROM valid_history
    WHERE observation_rank = 2
)
SELECT
    latest.*,
    previous.snapshot_date AS previous_snapshot_date,
    previous.scene_id AS previous_scene_id,
    previous.valid_fraction AS previous_valid_fraction,
    previous.ndvi AS previous_ndvi,
    previous.ndmi AS previous_ndmi,
    previous.bsi AS previous_bsi,
    previous.fvc_proxy AS previous_fvc_proxy,
    previous.nirv AS previous_nirv
FROM latest
LEFT JOIN previous
  ON previous.farm_id = latest.farm_id
 AND previous.h3_index = latest.h3_index;

COMMENT ON VIEW h3_latest_valid_observations_v1 IS
'Latest independently valid observation per farm H3 cell, plus its previous valid observation. It is a temporal mosaic and may contain different source dates.';

COMMIT;