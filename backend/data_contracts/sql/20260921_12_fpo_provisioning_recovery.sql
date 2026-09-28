BEGIN;

ALTER TABLE public.fpo_organizations
    ADD COLUMN IF NOT EXISTS provisioning_error text;

CREATE INDEX IF NOT EXISTS idx_fpo_org_provisioning_status
    ON public.fpo_organizations (provisioning_status, updated_at DESC);

COMMIT;
