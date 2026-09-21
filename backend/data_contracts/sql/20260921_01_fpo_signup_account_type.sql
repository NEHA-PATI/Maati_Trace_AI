BEGIN;

-- MaatiTrace FPO phase 1: make normal signup account-type aware.
-- This migration is additive. Do not edit previously applied migrations.

ALTER TABLE public.signup_otp_sessions
    ADD COLUMN IF NOT EXISTS account_type text NOT NULL DEFAULT 'farmer',
    ADD COLUMN IF NOT EXISTS signup_profile_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS authorised_fpo_representative boolean NOT NULL DEFAULT false;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_signup_otp_account_type'
    ) THEN
        ALTER TABLE public.signup_otp_sessions
            ADD CONSTRAINT ck_signup_otp_account_type
            CHECK (account_type IN ('farmer', 'fpo'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_signup_otp_account_type_active
    ON public.signup_otp_sessions (account_type, created_at DESC)
    WHERE completed_at IS NULL AND invalidated_at IS NULL;

-- Auth publishes domain events transactionally. Consumers acknowledge them later.
CREATE TABLE IF NOT EXISTS public.auth_outbox_events (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type text NOT NULL,
    event_version integer NOT NULL DEFAULT 1,
    subject_id uuid NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'queued',
    attempts integer NOT NULL DEFAULT 0,
    available_at timestamptz NOT NULL DEFAULT now(),
    locked_at timestamptz,
    published_at timestamptz,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_auth_outbox_status
        CHECK (status IN ('queued', 'publishing', 'published', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_auth_outbox_pending
    ON public.auth_outbox_events (status, available_at, created_at)
    WHERE status IN ('queued', 'failed');

CREATE INDEX IF NOT EXISTS idx_auth_outbox_subject
    ON public.auth_outbox_events (subject_id, created_at DESC);

COMMIT;
