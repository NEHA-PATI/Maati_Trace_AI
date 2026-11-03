BEGIN;

-- Durable source identity prevents repeated downloads and raster processing.
CREATE TABLE IF NOT EXISTS public.farm_dataset_source_versions (
    source_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    dataset_key TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    source_datetime TIMESTAMPTZ,
    period_start DATE,
    period_end DATE,
    processing_version TEXT NOT NULL,
    content_hash TEXT,
    row_fingerprint TEXT,
    materialization_status TEXT NOT NULL DEFAULT 'materialized'
        CHECK (materialization_status IN ('discovered', 'materializing', 'materialized', 'stale', 'failed')),
    parquet_uri TEXT,
    row_count BIGINT NOT NULL DEFAULT 0,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_dataset_source_version
        UNIQUE (farm_id, dataset_key, source_item_id, processing_version)
);

CREATE INDEX IF NOT EXISTS idx_farm_dataset_source_latest
    ON public.farm_dataset_source_versions(farm_id, dataset_key, source_datetime DESC NULLS LAST);

-- A materialization is valid only for the exact farm geometry/H3 set/version.
CREATE TABLE IF NOT EXISTS public.farm_dataset_materializations (
    materialization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    dataset_key TEXT NOT NULL,
    boundary_hash TEXT NOT NULL,
    h3_resolution INTEGER NOT NULL,
    h3_index_set_hash TEXT NOT NULL,
    dataset_version TEXT,
    source_version TEXT,
    processing_version TEXT,
    materialization_version TEXT NOT NULL,
    materialization_fingerprint TEXT NOT NULL,
    row_count BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_dataset_materialization UNIQUE (farm_id, dataset_key)
);

ALTER TABLE public.farm_dataset_state
    ADD COLUMN IF NOT EXISTS boundary_hash TEXT,
    ADD COLUMN IF NOT EXISTS h3_resolution INTEGER,
    ADD COLUMN IF NOT EXISTS h3_index_set_hash TEXT,
    ADD COLUMN IF NOT EXISTS dataset_version TEXT,
    ADD COLUMN IF NOT EXISTS source_version TEXT,
    ADD COLUMN IF NOT EXISTS materialization_version TEXT,
    ADD COLUMN IF NOT EXISTS materialization_fingerprint TEXT,
    ADD COLUMN IF NOT EXISTS latest_source_item_id TEXT,
    ADD COLUMN IF NOT EXISTS latest_content_hash TEXT,
    ADD COLUMN IF NOT EXISTS latest_row_fingerprint TEXT;

-- Explicit analysis-run ledger. Existing pipeline_jobs remain the operational
-- job log; this table is the farmer-visible completed-run contract.
CREATE TABLE IF NOT EXISTS public.analysis_runs (
    analysis_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    pipeline_job_id UUID REFERENCES public.pipeline_jobs(job_id) ON DELETE SET NULL,
    run_mode TEXT NOT NULL DEFAULT 'incremental_latest'
        CHECK (run_mode IN ('bootstrap', 'incremental_latest', 'manual')),
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'completed_with_warnings', 'failed')),
    requested_start_date DATE,
    requested_end_date DATE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    result_date DATE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_analysis_run_pipeline_job UNIQUE (pipeline_job_id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_latest
    ON public.analysis_runs(farm_id, status, finished_at DESC NULLS LAST);

COMMIT;
