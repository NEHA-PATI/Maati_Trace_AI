BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_farmer_relationships (
    relationship_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE RESTRICT,
    farmer_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    farmer_profile_id uuid REFERENCES public.farmer_profiles(farmer_id) ON DELETE SET NULL,
    relationship_type varchar(30) NOT NULL DEFAULT 'PRIMARY',
    status varchar(50) NOT NULL DEFAULT 'PENDING_FPO_ACCEPTANCE',
    initiated_by varchar(30) NOT NULL,
    farmer_consented_at timestamptz NOT NULL,
    fpo_accepted_at timestamptz,
    fpo_accepted_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    revoked_at timestamptz,
    revoked_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    revocation_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_farmer_relationship_type CHECK (relationship_type IN ('PRIMARY')),
    CONSTRAINT ck_fpo_farmer_relationship_status CHECK (status IN ('PENDING_FPO_ACCEPTANCE', 'ACTIVE', 'REJECTED', 'REVOKED', 'ACTIVE_LEGACY_PENDING_CONSENT')),
    CONSTRAINT ck_fpo_farmer_relationship_initiator CHECK (initiated_by IN ('FARMER', 'FPO', 'LEGACY_MIGRATION'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_farmer_active_primary
    ON public.fpo_farmer_relationships (farmer_user_id)
    WHERE relationship_type = 'PRIMARY' AND status = 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_farmer_open_request
    ON public.fpo_farmer_relationships (fpo_id, farmer_user_id)
    WHERE status = 'PENDING_FPO_ACCEPTANCE';

CREATE INDEX IF NOT EXISTS idx_fpo_farmer_relationship_fpo_status
    ON public.fpo_farmer_relationships (fpo_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fpo_farmer_relationship_farmer_status
    ON public.fpo_farmer_relationships (farmer_user_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_farmer_relationship_events (
    relationship_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE CASCADE,
    event_type varchar(50) NOT NULL,
    actor_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_farmer_relationship_event_type CHECK (event_type IN ('REQUESTED', 'CONSENT_RECORDED', 'ACCEPTED', 'REJECTED', 'REVOKED'))
);

CREATE INDEX IF NOT EXISTS idx_fpo_farmer_relationship_events_history
    ON public.fpo_farmer_relationship_events (relationship_id, created_at DESC);

COMMIT;
