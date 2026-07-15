-- 006_pipeline_jobs_schema_update.sql
-- Updates the existing pipeline_jobs table schema to support farm-centric pipeline job tracking.

BEGIN;

ALTER TABLE pipeline_jobs
    ADD COLUMN IF NOT EXISTS job_id UUID DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS farm_id UUID,
    ADD COLUMN IF NOT EXISTS current_stage TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now(),
    ADD COLUMN IF NOT EXISTS error_code TEXT,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_farm_id ON pipeline_jobs(farm_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status ON pipeline_jobs(status);

COMMIT;
