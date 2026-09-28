BEGIN;

-- A farm may have active consent-backed relationships with multiple FPOs.
-- Keep uniqueness only for the same farm/FPO pair; consent and API checks
-- continue to scope each FPO to this exact farm.
DROP INDEX IF EXISTS public.uq_fpo_farm_active_primary;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_farm_fpo_active
    ON public.fpo_farmer_relationships (farm_id, fpo_id)
    WHERE farm_id IS NOT NULL
      AND relationship_type = 'PRIMARY'
      AND status = 'ACTIVE';

COMMIT;
