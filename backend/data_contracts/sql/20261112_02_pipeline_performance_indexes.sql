BEGIN;

-- Composite indexes used by the feature-engine source bundle and trend stage.
CREATE INDEX IF NOT EXISTS ix_h3_sentinel2_farm_h3_snapshot
    ON public.h3_sentinel2_features (farm_id, h3_index, snapshot_date DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_h3_sentinel1_farm_h3_snapshot
    ON public.h3_sentinel1_features (farm_id, h3_index, snapshot_date DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_h3_landsat_farm_h3_snapshot
    ON public.h3_landsat_features (farm_id, h3_index, snapshot_date DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_farm_weather_farm_observation
    ON public.farm_weather_observations (farm_id, observation_date DESC);
CREATE INDEX IF NOT EXISTS ix_farm_reanalysis_farm_observation
    ON public.farm_reanalysis_daily (farm_id, observation_date DESC);
CREATE INDEX IF NOT EXISTS ix_farm_smap_farm_observed
    ON public.farm_smap_observations (farm_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_farm_grid_crosswalk_farm_cell
    ON public.farm_grid_h3_crosswalk (farm_id, grid_cell_id, h3_index);

COMMIT;
