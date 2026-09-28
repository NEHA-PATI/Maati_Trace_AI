BEGIN;

-- FPO organization identity is separate from the Auth user identity.
-- Provisioning workers populate this table from auth.user.created events.

CREATE SEQUENCE IF NOT EXISTS public.fpo_public_number_seq
    START WITH 100001
    INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS public.fpo_organizations (
    fpo_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id uuid NOT NULL UNIQUE REFERENCES public.users(user_id) ON DELETE RESTRICT,
    public_fpo_id varchar(40) NOT NULL UNIQUE,
    lifecycle_status varchar(40) NOT NULL DEFAULT 'ONBOARDING',
    provisioning_status varchar(40) NOT NULL DEFAULT 'PENDING',
    verification_status varchar(40) NOT NULL DEFAULT 'PROFILE_INCOMPLETE',
    verification_level varchar(30),
    commercial_status varchar(30) NOT NULL DEFAULT 'UNASSIGNED',
    discoverable boolean NOT NULL DEFAULT false,
    approved_at timestamptz,
    approved_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    suspended_at timestamptz,
    suspension_reason text,
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_org_lifecycle CHECK (lifecycle_status IN ('ONBOARDING', 'ACTIVE', 'SUSPENDED', 'CLOSED')),
    CONSTRAINT ck_fpo_org_provisioning CHECK (provisioning_status IN ('PENDING', 'PROFILE_PENDING', 'READY', 'FAILED')),
    CONSTRAINT ck_fpo_org_verification CHECK (verification_status IN ('PROFILE_INCOMPLETE', 'READY_TO_SUBMIT', 'SUBMITTED', 'UNDER_REVIEW', 'CHANGES_REQUIRED', 'APPROVED', 'REJECTED', 'SUSPENDED'))
);

CREATE INDEX IF NOT EXISTS idx_fpo_org_verification
    ON public.fpo_organizations (verification_status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fpo_org_discovery
    ON public.fpo_organizations (discoverable, verification_status)
    WHERE discoverable = true;

COMMIT;
