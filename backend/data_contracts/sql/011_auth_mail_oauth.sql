BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- =========================================================
-- 1. USERS AUTHENTICATION FIELDS
-- =========================================================

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS full_name TEXT,
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS profile_image_url TEXT,
    ADD COLUMN IF NOT EXISTS onboarding_status TEXT NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();


-- =========================================================
-- 2. SIGNUP OTP SESSIONS
-- This table was originally expected from migration 004.
-- It is also created here so migration 011 is independently safe.
-- =========================================================

CREATE TABLE IF NOT EXISTS signup_otp_sessions (
    signup_session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    full_name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    email TEXT,

    password_hash TEXT NOT NULL,

    role TEXT NOT NULL DEFAULT 'farmer',
    fpo_id TEXT,
    invite_code TEXT,

    otp_hash TEXT NOT NULL,
    otp_expires_at TIMESTAMPTZ NOT NULL,

    verified_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    locked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE signup_otp_sessions
    ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_signup_otp_expiry
    ON signup_otp_sessions (otp_expires_at)
    WHERE completed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_signup_otp_email
    ON signup_otp_sessions (lower(email))
    WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_signup_otp_phone
    ON signup_otp_sessions (phone_number);

CREATE INDEX IF NOT EXISTS idx_signup_otp_active_session
    ON signup_otp_sessions (signup_session_id, otp_expires_at)
    WHERE verified_at IS NULL
      AND completed_at IS NULL
      AND locked_at IS NULL;


-- =========================================================
-- 3. REFRESH TOKENS
-- Only token hashes are stored.
-- =========================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    refresh_token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_active
    ON refresh_tokens (token_hash, expires_at)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user
    ON refresh_tokens (user_id, created_at DESC);


-- =========================================================
-- 4. EXTERNAL AUTH IDENTITIES
-- Google identity is linked to one existing MaatiTrace user.
-- =========================================================

CREATE TABLE IF NOT EXISTS auth_identities (
    auth_identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    provider TEXT NOT NULL,
    provider_subject TEXT NOT NULL,

    email TEXT,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    raw_profile JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_auth_identity_provider_subject
        UNIQUE (provider, provider_subject),

    CONSTRAINT chk_auth_identity_provider
        CHECK (provider IN ('google'))
);

CREATE INDEX IF NOT EXISTS idx_auth_identities_user
    ON auth_identities (user_id);

CREATE INDEX IF NOT EXISTS idx_auth_identities_email
    ON auth_identities (lower(email))
    WHERE email IS NOT NULL;


-- =========================================================
-- 5. EMAIL DELIVERY AUDIT
-- Does not store the actual OTP.
-- =========================================================

CREATE TABLE IF NOT EXISTS email_outbox (
    email_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    to_email TEXT NOT NULL,
    to_name TEXT,

    subject TEXT NOT NULL,
    template_key TEXT NOT NULL,

    provider TEXT NOT NULL,
    provider_message_id TEXT,

    status TEXT NOT NULL,
    error_message TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,

    CONSTRAINT chk_email_outbox_status
        CHECK (status IN ('pending', 'sent', 'failed')),

    CONSTRAINT chk_email_outbox_provider
        CHECK (provider IN ('console', 'brevo'))
);

CREATE INDEX IF NOT EXISTS idx_email_outbox_created
    ON email_outbox (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_email_outbox_status
    ON email_outbox (status, created_at DESC);


COMMIT;