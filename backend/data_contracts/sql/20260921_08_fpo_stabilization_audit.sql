BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_audit_events (
    audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid REFERENCES public.fpo_organizations(fpo_id) ON DELETE SET NULL,
    actor_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    action varchar(100) NOT NULL,
    target_type varchar(80),
    target_id uuid,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fpo_audit_events_fpo_time
    ON public.fpo_audit_events (fpo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fpo_audit_events_action_time
    ON public.fpo_audit_events (action, created_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_reconciliation_runs (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    started_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    status varchar(30) NOT NULL DEFAULT 'RUNNING',
    repaired_farmer_projections integer NOT NULL DEFAULT 0,
    cleared_stale_projections integer NOT NULL DEFAULT 0,
    orphaned_organizations integer NOT NULL DEFAULT 0,
    completed_at timestamptz,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_reconciliation_status CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED'))
);

CREATE INDEX IF NOT EXISTS idx_fpo_reconciliation_runs_time
    ON public.fpo_reconciliation_runs (created_at DESC);

COMMIT;
