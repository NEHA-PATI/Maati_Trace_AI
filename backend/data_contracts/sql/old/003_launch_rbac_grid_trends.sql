CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS fpo_users (
    fpo_user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id UUID NOT NULL REFERENCES fpos(fpo_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('fpo_admin', 'fpo_manager', 'field_officer')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_user UNIQUE (fpo_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_fpo_users_fpo_id ON fpo_users(fpo_id);
CREATE INDEX IF NOT EXISTS idx_fpo_users_user_id ON fpo_users(user_id);

ALTER TABLE farmer_profiles
ADD COLUMN IF NOT EXISTS user_id UUID NULL REFERENCES users(user_id);

CREATE INDEX IF NOT EXISTS idx_farmer_profiles_user_id
ON farmer_profiles(user_id);

CREATE TABLE IF NOT EXISTS farm_h3_daily_trends (
    trend_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(farm_id) ON DELETE CASCADE,
    farmer_id UUID NOT NULL REFERENCES farmer_profiles(farmer_id),
    fpo_id UUID NULL REFERENCES fpos(fpo_id),
    h3_index BIGINT NOT NULL,
    h3_resolution INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    ndvi DOUBLE PRECISION NULL,
    ndmi DOUBLE PRECISION NULL,
    ndwi DOUBLE PRECISION NULL,
    bsi DOUBLE PRECISION NULL,
    evi DOUBLE PRECISION NULL,
    savi DOUBLE PRECISION NULL,
    msi DOUBLE PRECISION NULL,
    nbr DOUBLE PRECISION NULL,
    ndre DOUBLE PRECISION NULL,
    ndvi_change DOUBLE PRECISION NULL,
    ndmi_change DOUBLE PRECISION NULL,
    bsi_change DOUBLE PRECISION NULL,
    vegetation_trend TEXT NULL CHECK (vegetation_trend IN ('improving', 'stable', 'degrading', 'unknown')),
    moisture_trend TEXT NULL CHECK (moisture_trend IN ('improving', 'stable', 'degrading', 'unknown')),
    soil_exposure_trend TEXT NULL CHECK (soil_exposure_trend IN ('improving', 'stable', 'degrading', 'unknown')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_h3_daily_trend UNIQUE (farm_id, h3_index, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_farm_h3_daily_trends_farm
ON farm_h3_daily_trends(farm_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_h3_daily_trends_farmer
ON farm_h3_daily_trends(farmer_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_h3_daily_trends_fpo
ON farm_h3_daily_trends(fpo_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_h3_daily_trends_h3
ON farm_h3_daily_trends(h3_index);

CREATE TABLE IF NOT EXISTS farm_grid_cells (
    grid_cell_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(farm_id) ON DELETE CASCADE,
    grid_size_meters INTEGER NOT NULL DEFAULT 10,
    grid_row INTEGER NOT NULL,
    grid_col INTEGER NOT NULL,
    cell_polygon_geojson JSONB NOT NULL,
    cell_centroid_lon DOUBLE PRECISION NOT NULL,
    cell_centroid_lat DOUBLE PRECISION NOT NULL,
    coverage_ratio DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_grid_cell UNIQUE (farm_id, grid_size_meters, grid_row, grid_col)
);

CREATE INDEX IF NOT EXISTS idx_farm_grid_cells_farm ON farm_grid_cells(farm_id);
CREATE INDEX IF NOT EXISTS idx_farm_grid_cells_grid_size ON farm_grid_cells(farm_id, grid_size_meters);

CREATE TABLE IF NOT EXISTS farm_grid_h3_crosswalk (
    crosswalk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(farm_id) ON DELETE CASCADE,
    grid_cell_id UUID NOT NULL REFERENCES farm_grid_cells(grid_cell_id) ON DELETE CASCADE,
    h3_index BIGINT NOT NULL,
    h3_resolution INTEGER NOT NULL,
    overlap_ratio DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_grid_h3_crosswalk UNIQUE (farm_id, grid_cell_id, h3_index)
);

CREATE INDEX IF NOT EXISTS idx_farm_grid_h3_crosswalk_farm ON farm_grid_h3_crosswalk(farm_id);
CREATE INDEX IF NOT EXISTS idx_farm_grid_h3_crosswalk_h3 ON farm_grid_h3_crosswalk(h3_index);

CREATE TABLE IF NOT EXISTS farm_grid_daily_values (
    grid_value_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(farm_id) ON DELETE CASCADE,
    grid_cell_id UUID NOT NULL REFERENCES farm_grid_cells(grid_cell_id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    ndvi DOUBLE PRECISION NULL,
    ndmi DOUBLE PRECISION NULL,
    ndwi DOUBLE PRECISION NULL,
    bsi DOUBLE PRECISION NULL,
    evi DOUBLE PRECISION NULL,
    savi DOUBLE PRECISION NULL,
    msi DOUBLE PRECISION NULL,
    nbr DOUBLE PRECISION NULL,
    ndre DOUBLE PRECISION NULL,
    ndvi_change DOUBLE PRECISION NULL,
    ndmi_change DOUBLE PRECISION NULL,
    bsi_change DOUBLE PRECISION NULL,
    vegetation_trend TEXT NULL,
    moisture_trend TEXT NULL,
    soil_exposure_trend TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_grid_daily_value UNIQUE (farm_id, grid_cell_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_farm_grid_daily_values_farm
ON farm_grid_daily_values(farm_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_grid_daily_values_cell
ON farm_grid_daily_values(grid_cell_id, snapshot_date DESC);
