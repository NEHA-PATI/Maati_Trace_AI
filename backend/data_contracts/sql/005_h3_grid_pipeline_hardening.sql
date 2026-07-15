-- 005_h3_grid_pipeline_hardening.sql
-- Adds pipeline_jobs table and hardening indexes for h3_sentinel2_features

BEGIN;

-- Pipeline jobs table
CREATE TABLE IF NOT EXISTS pipeline_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    service_name TEXT NOT NULL DEFAULT 'hot_stream_orchestrator_service',
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending/running/succeeded/failed/partial
    current_stage TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_farm_id ON pipeline_jobs(farm_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status ON pipeline_jobs(status);

-- Ensure uniqueness for h3 features per farm/h3/snapshot/scene
CREATE UNIQUE INDEX IF NOT EXISTS uq_h3_sentinel2_features_farm_h3_scene
    ON h3_sentinel2_features(farm_id, h3_index, snapshot_date, scene_id);

-- Additional useful indexes
CREATE INDEX IF NOT EXISTS idx_h3_features_farm_snapshot ON h3_sentinel2_features(farm_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_h3_features_farm_h3 ON h3_sentinel2_features(farm_id, h3_index);
CREATE INDEX IF NOT EXISTS idx_h3_features_farmer_snapshot ON h3_sentinel2_features(farmer_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_h3_features_fpo_snapshot ON h3_sentinel2_features(fpo_id, snapshot_date);

COMMIT;
