BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_class_c_release_checks (
    check_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), plan_version_id uuid NOT NULL REFERENCES public.fpo_plan_versions(plan_version_id) ON DELETE CASCADE,
    check_key text NOT NULL, status text NOT NULL, evidence jsonb NOT NULL DEFAULT '{}'::jsonb, checked_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL, checked_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (plan_version_id,check_key), CONSTRAINT ck_fpo_class_c_release_status CHECK (status IN ('PASS','FAIL','WAIVED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_class_c_release_checks_plan ON public.fpo_class_c_release_checks (plan_version_id,status);

ALTER TABLE public.fpo_plan_versions
    ADD COLUMN IF NOT EXISTS release_state varchar(25) NOT NULL DEFAULT 'DRAFT';

COMMIT;
