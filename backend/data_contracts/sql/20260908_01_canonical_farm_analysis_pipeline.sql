BEGIN;

-- Canonical farmer-visible farm registration / latest-analysis workflow.
-- Keep this migration idempotent because older installations may already have
-- pipeline_jobs from the legacy operational migrations.
CREATE TABLE IF NOT EXISTS public.pipeline_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID,
    service_name TEXT NOT NULL DEFAULT 'hot_stream_orchestrator_service',
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    current_stage TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE public.pipeline_jobs
    ADD COLUMN IF NOT EXISTS farm_id UUID,
    ADD COLUMN IF NOT EXISTS current_stage TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now(),
    ADD COLUMN IF NOT EXISTS error_code TEXT,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

UPDATE public.pipeline_jobs
SET updated_at = COALESCE(updated_at, started_at, now()),
    metadata = COALESCE(metadata, '{}'::jsonb)
WHERE updated_at IS NULL OR metadata IS NULL;

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_farm_type_started
    ON public.pipeline_jobs(farm_id, job_type, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_farm_active
    ON public.pipeline_jobs(farm_id, status)
    WHERE status IN ('pending', 'running');

COMMIT;
