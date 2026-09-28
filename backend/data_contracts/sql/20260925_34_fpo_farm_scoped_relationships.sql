BEGIN;

-- Farm-scoped FPO access.  The existing relationship table is retained because
-- Class B/C contracts reference its relationship_id.  New rows must identify
-- the exact farm; legacy rows remain available only for migration/reconciliation.
ALTER TABLE public.fpo_farmer_relationships
    ADD COLUMN IF NOT EXISTS farm_id uuid REFERENCES public.farms(farm_id) ON DELETE RESTRICT;

ALTER TABLE public.fpo_farmer_relationships
    DROP CONSTRAINT IF EXISTS ck_fpo_farmer_relationship_status;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_fpo_farmer_relationship_status_farm_scoped'
          AND conrelid = 'public.fpo_farmer_relationships'::regclass
    ) THEN
        ALTER TABLE public.fpo_farmer_relationships
            ADD CONSTRAINT ck_fpo_farmer_relationship_status_farm_scoped
            CHECK (status IN ('PENDING_FPO_ACCEPTANCE', 'ACTIVE', 'REJECTED', 'REVOKED', 'CANCELLED', 'ACTIVE_LEGACY_PENDING_CONSENT'));
    END IF;
END;
$$;

ALTER TABLE public.fpo_farmer_relationship_events
    DROP CONSTRAINT IF EXISTS ck_fpo_farmer_relationship_event_type;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_fpo_farmer_relationship_event_type_farm_scoped'
          AND conrelid = 'public.fpo_farmer_relationship_events'::regclass
    ) THEN
        ALTER TABLE public.fpo_farmer_relationship_events
            ADD CONSTRAINT ck_fpo_farmer_relationship_event_type_farm_scoped
            CHECK (event_type IN (
                'REQUESTED', 'CONSENT_RECORDED', 'ACCEPTED', 'REJECTED', 'REVOKED',
                'REQUEST_CANCELLED', 'TERMINATED_BY_FPO'
            ));
    END IF;
END;
$$;

-- The old indexes enforced one relationship per farmer.  Farm access must be
-- independent: one farmer may connect different farms to different FPOs.
DROP INDEX IF EXISTS public.uq_fpo_farmer_active_primary;
DROP INDEX IF EXISTS public.uq_fpo_one_open_or_active_relationship;
DROP INDEX IF EXISTS public.uq_fpo_farmer_open_request;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_farm_active_primary
    ON public.fpo_farmer_relationships (farm_id)
    WHERE farm_id IS NOT NULL AND relationship_type = 'PRIMARY' AND status = 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_farm_open_request
    ON public.fpo_farmer_relationships (fpo_id, farm_id)
    WHERE farm_id IS NOT NULL AND status = 'PENDING_FPO_ACCEPTANCE';

CREATE INDEX IF NOT EXISTS idx_fpo_farm_relationship_farm_status
    ON public.fpo_farmer_relationships (farm_id, status, created_at DESC);

COMMIT;
