BEGIN;

-- Additive follow-up for deployments where 20260921_03 is already applied.
-- Links FPO Management organization identity to the Profile Service FPO row.

ALTER TABLE public.fpo_organizations
    ADD COLUMN IF NOT EXISTS profile_fpo_id uuid
        REFERENCES public.fpos(fpo_id) ON DELETE SET NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_org_profile_fpo
    ON public.fpo_organizations (profile_fpo_id)
    WHERE profile_fpo_id IS NOT NULL;

COMMIT;
