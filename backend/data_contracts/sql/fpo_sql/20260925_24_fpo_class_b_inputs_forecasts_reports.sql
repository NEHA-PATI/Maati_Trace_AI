BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_input_demand_plans (
    input_plan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    season_plan_id uuid NOT NULL REFERENCES public.fpo_season_plans(season_plan_id) ON DELETE RESTRICT, name varchar(200) NOT NULL,
    status text NOT NULL DEFAULT 'DRAFT', calculation_version text NOT NULL DEFAULT 'inputs-v1', calculated_at timestamptz,
    created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_input_plan_status CHECK (status IN ('DRAFT','CALCULATED','LOCKED','ARCHIVED'))
);
CREATE TABLE IF NOT EXISTS public.fpo_input_demand_items (
    input_demand_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), input_plan_id uuid NOT NULL REFERENCES public.fpo_input_demand_plans(input_plan_id) ON DELETE CASCADE,
    crop_code text NOT NULL, stage_code text, input_category text NOT NULL, input_code text NOT NULL, input_name text NOT NULL,
    farmer_count integer NOT NULL DEFAULT 0, area_acres numeric(16,4) NOT NULL DEFAULT 0, required_quantity numeric(18,4) NOT NULL DEFAULT 0,
    quantity_unit text NOT NULL, calculation_basis jsonb NOT NULL DEFAULT '{}'::jsonb, confidence text NOT NULL DEFAULT 'MEDIUM', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_input_category CHECK (input_category IN ('SEED','NUTRIENT','CROP_PROTECTION','OTHER')), CONSTRAINT ck_fpo_input_confidence CHECK (confidence IN ('LOW','MEDIUM','HIGH'))
);
CREATE TABLE IF NOT EXISTS public.fpo_yield_forecasts (
    yield_forecast_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    season_plan_id uuid REFERENCES public.fpo_season_plans(season_plan_id) ON DELETE SET NULL, scope_type text NOT NULL, farmer_id uuid, farm_id uuid,
    crop_code text NOT NULL, variety_code text, forecast_date date NOT NULL DEFAULT current_date, forecast_yield_value numeric(18,4) NOT NULL, forecast_yield_unit text NOT NULL,
    forecast_production_value numeric(18,4), forecast_production_unit text, lower_bound numeric(18,4), upper_bound numeric(18,4), confidence_score numeric(6,5),
    model_key text NOT NULL, model_version text NOT NULL, feature_snapshot_id text, input_data_through timestamptz NOT NULL, quality_status text NOT NULL,
    explanation_codes text[] NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_forecast_scope CHECK (scope_type IN ('FARM','CROP','SEGMENT','PORTFOLIO')), CONSTRAINT ck_fpo_forecast_quality CHECK (quality_status IN ('VALID','LOW_COVERAGE','STALE','INSUFFICIENT_DATA')),
    UNIQUE (scope_type,farm_id,crop_code,forecast_date,model_version)
);
CREATE TABLE IF NOT EXISTS public.fpo_report_jobs (
    report_job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    report_type text NOT NULL, format text NOT NULL, parameters jsonb NOT NULL DEFAULT '{}'::jsonb, parameter_schema_version integer NOT NULL DEFAULT 1,
    status text NOT NULL DEFAULT 'QUEUED', requested_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, requested_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz, completed_at timestamptz, expires_at timestamptz NOT NULL DEFAULT (now()+interval '30 days'), row_count integer,
    error_code text, error_message text, idempotency_key text NOT NULL, CONSTRAINT ck_fpo_report_format CHECK (format IN ('CSV','XLSX','PDF')),
    CONSTRAINT ck_fpo_report_status CHECK (status IN ('QUEUED','RUNNING','COMPLETED','FAILED','CANCELLED','EXPIRED')), UNIQUE (fpo_id,idempotency_key)
);
CREATE TABLE IF NOT EXISTS public.fpo_report_artifacts (
    report_artifact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), report_job_id uuid NOT NULL REFERENCES public.fpo_report_jobs(report_job_id) ON DELETE CASCADE,
    object_key text NOT NULL, filename text NOT NULL, mime_type text NOT NULL, size_bytes bigint NOT NULL, checksum text NOT NULL, encryption_key_version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL, download_count integer NOT NULL DEFAULT 0, last_downloaded_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_fpo_report_jobs_queue ON public.fpo_report_jobs (status,requested_at);
CREATE INDEX IF NOT EXISTS idx_fpo_report_jobs_owner ON public.fpo_report_jobs (fpo_id,requested_at DESC);

COMMIT;
