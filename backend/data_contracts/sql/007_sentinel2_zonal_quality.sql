BEGIN;

DO $$
BEGIN
    IF to_regclass('public.h3_sentinel2_features') IS NULL THEN
        RAISE EXCEPTION
            'Required table public.h3_sentinel2_features does not exist';
    END IF;
END $$;

ALTER TABLE h3_sentinel2_features
    ADD COLUMN IF NOT EXISTS observed_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS valid_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cloud_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS shadow_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS water_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS snow_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS nodata_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS invalid_area_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS valid_fraction DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS fvc_proxy DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS nirv DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS optical_resolution_m INTEGER,
    ADD COLUMN IF NOT EXISTS rededge_swir_resolution_m INTEGER,
    ADD COLUMN IF NOT EXISTS processing_version TEXT;

CREATE INDEX IF NOT EXISTS idx_h3_s2_farm_scene_processing
ON h3_sentinel2_features (
    farm_id,
    snapshot_date DESC,
    scene_id,
    processing_version
);

CREATE INDEX IF NOT EXISTS idx_h3_s2_usable_area
ON h3_sentinel2_features (
    farm_id,
    snapshot_date DESC
)
WHERE valid_area_m2 > 0;

COMMENT ON COLUMN h3_sentinel2_features.fvc_proxy IS
'Fractional vegetation cover proxy from Sentinel-2 NDVI. It is not a crop-health score.';

COMMENT ON COLUMN h3_sentinel2_features.nirv IS
'Near-infrared reflectance of vegetation: NDVI multiplied by B08 reflectance.';

COMMENT ON COLUMN h3_sentinel2_features.valid_fraction IS
'Farm-clipped H3 valid observed area divided by observed area.';

COMMENT ON COLUMN h3_sentinel2_features.processing_version IS
'Null means legacy processing. s2_zonal_v1 means farm-clipped area-weighted statistics.';

COMMIT;