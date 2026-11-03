BEGIN;

ALTER TABLE public.fpo_bulk_import_rows
    DROP CONSTRAINT IF EXISTS ck_fpo_import_row_status;
ALTER TABLE public.fpo_bulk_import_rows
    DROP CONSTRAINT IF EXISTS ck_fpo_import_row_status_v2;
ALTER TABLE public.fpo_bulk_import_rows
    ADD CONSTRAINT ck_fpo_import_row_status_v2 CHECK (
        row_status IN ('PENDING','VALID','INVALID','STAGED','CREATED','UPDATED','SKIPPED','FAILED')
    );

ALTER TABLE public.fpo_bulk_import_jobs
    ADD COLUMN IF NOT EXISTS staged_rows integer NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS public.fpo_bulk_staged_records (
    staged_record_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    import_job_id uuid NOT NULL REFERENCES public.fpo_bulk_import_jobs(import_job_id) ON DELETE CASCADE,
    import_row_id uuid NOT NULL UNIQUE REFERENCES public.fpo_bulk_import_rows(import_row_id) ON DELETE CASCADE,
    record_type text NOT NULL,
    farmer_id uuid REFERENCES public.farmer_profiles(farmer_id) ON DELETE SET NULL,
    farm_id uuid,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'AWAITING_FARMER_ACCOUNT',
    status_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_bulk_staged_type CHECK (record_type IN ('FARMER','FARM')),
    CONSTRAINT ck_fpo_bulk_staged_status CHECK (
        status IN ('AWAITING_FARMER_ACCOUNT','AWAITING_FARM_CONFIRMATION','AWAITING_CONSENT','READY_FOR_RELATIONSHIP','CREATED','FAILED')
    )
);

CREATE INDEX IF NOT EXISTS idx_fpo_bulk_staged_owner
    ON public.fpo_bulk_staged_records (fpo_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fpo_bulk_staged_farmer
    ON public.fpo_bulk_staged_records (farmer_id, status);

COMMIT;
