BEGIN;

-- Per-farm source readiness is deliberately separate from pipeline_jobs. A
-- pipeline run is an attempt; this table is the durable latest truth for a
-- dataset and is consumed by status/admin/intelligence confidence views.
CREATE TABLE IF NOT EXISTS public.farm_dataset_state (
    farm_dataset_state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    dataset_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'never_run'
        CHECK (status IN ('never_run', 'queued', 'running', 'ready', 'partial', 'stale', 'failed')),
    spatial_level TEXT,
    native_resolution_m DOUBLE PRECISION,
    last_attempt_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    latest_observation_at TIMESTAMPTZ,
    history_start DATE,
    history_end DATE,
    row_count BIGINT NOT NULL DEFAULT 0,
    processing_version TEXT,
    provider TEXT,
    retryable BOOLEAN NOT NULL DEFAULT FALSE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_dataset_state UNIQUE (farm_id, dataset_key)
);

CREATE INDEX IF NOT EXISTS idx_farm_dataset_state_farm
    ON public.farm_dataset_state(farm_id);
CREATE INDEX IF NOT EXISTS idx_farm_dataset_state_status
    ON public.farm_dataset_state(status);
CREATE INDEX IF NOT EXISTS idx_farm_dataset_state_retry
    ON public.farm_dataset_state(next_retry_at)
    WHERE retryable = TRUE;

-- Explicit stage rows keep the existing metadata contract backwards
-- compatible while making every stage/dataset independently queryable.
CREATE TABLE IF NOT EXISTS public.pipeline_job_steps (
    step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.pipeline_jobs(job_id) ON DELETE CASCADE,
    farm_id UUID REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    stage_key TEXT NOT NULL,
    dataset_key TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    attempt INTEGER NOT NULL DEFAULT 1,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    rows_read BIGINT,
    rows_written BIGINT,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_pipeline_job_step UNIQUE (job_id, stage_key, dataset_key)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_job_steps_job
    ON public.pipeline_job_steps(job_id, created_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_job_steps_farm
    ON public.pipeline_job_steps(farm_id, created_at DESC);

-- Make source spatial semantics available in every observation table. The
-- existing source_resolution/native_resolution columns remain for backwards
-- compatibility; these columns are the normalized cross-source contract.
ALTER TABLE public.h3_sentinel1_features
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'h3',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.h3_landsat_features
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'h3',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.farm_weather_observations
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'regional',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.h3_terrain_features
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'static_h3',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.h3_landcover_features
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'static_h3',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.h3_surface_water_features
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'static_h3',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.farm_reanalysis_daily
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'regional',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.h3_soilgrids_features
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'static_h3',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.farm_smap_observations
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'regional',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.farm_modis_et_observations
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'regional',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.farm_modis_vegetation_observations
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'regional',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
ALTER TABLE public.farm_weather_forecasts
    ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'forecast',
    ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;

-- h3_sentinel2_features is created by the operational schema on older
-- installations, so use conditional ALTER statements only.
DO $$
BEGIN
    IF to_regclass('public.h3_sentinel2_features') IS NOT NULL THEN
        ALTER TABLE public.h3_sentinel2_features
            ADD COLUMN IF NOT EXISTS spatial_level TEXT DEFAULT 'h3',
            ADD COLUMN IF NOT EXISTS native_resolution_m DOUBLE PRECISION;
    END IF;
END $$;

COMMIT;
