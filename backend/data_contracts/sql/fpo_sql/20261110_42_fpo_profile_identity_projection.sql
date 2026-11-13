-- FPO-02: expose organization identity alongside the editable profile.
-- The public FPO ID belongs to fpo_organizations, not fpos.
-- This migration is intentionally additive and safe for existing data.
BEGIN;

CREATE INDEX IF NOT EXISTS ix_fpo_organizations_profile_fpo_id
    ON public.fpo_organizations (profile_fpo_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fpo_organizations_public_fpo_id
    ON public.fpo_organizations (public_fpo_id)
    WHERE public_fpo_id IS NOT NULL;

COMMIT;
