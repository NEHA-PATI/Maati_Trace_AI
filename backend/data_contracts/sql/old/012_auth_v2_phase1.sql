BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Stop with a clear message before creating unique indexes if legacy duplicates exist.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM users
        WHERE email IS NOT NULL
        GROUP BY lower(email)
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate case-insensitive emails exist in users. Resolve them before this migration.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM users
        WHERE phone_number IS NOT NULL
        GROUP BY phone_number
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate phone numbers exist in users. Resolve them before this migration.';
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_ci
    ON users (lower(email))
    WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_phone_number
    ON users (phone_number)
    WHERE phone_number IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_auth_identity_provider_subject
    ON auth_identities (provider, provider_subject);

CREATE UNIQUE INDEX IF NOT EXISTS uq_refresh_tokens_token_hash
    ON refresh_tokens (token_hash);

CREATE INDEX IF NOT EXISTS idx_farmer_profiles_user_id
    ON farmer_profiles (user_id);

-- Google-only accounts do not require a hidden random password.
ALTER TABLE users
    ALTER COLUMN password_hash DROP NOT NULL;

-- Signup OTP lifecycle and abuse-control fields.
ALTER TABLE signup_otp_sessions
    ADD COLUMN IF NOT EXISTS resend_count integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_sent_at timestamptz,
    ADD COLUMN IF NOT EXISTS invalidated_at timestamptz,
    ADD COLUMN IF NOT EXISTS invalidated_reason text,
    ADD COLUMN IF NOT EXISTS superseded_by_session_id uuid,
    ADD COLUMN IF NOT EXISTS created_ip inet,
    ADD COLUMN IF NOT EXISTS device_id_hash text,
    ADD COLUMN IF NOT EXISTS correlation_id text;

UPDATE signup_otp_sessions
SET last_sent_at = COALESCE(last_sent_at, now())
WHERE last_sent_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_signup_otp_email_active
    ON signup_otp_sessions (lower(email), otp_expires_at)
    WHERE completed_at IS NULL AND invalidated_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_signup_otp_phone_active
    ON signup_otp_sessions (phone_number, otp_expires_at)
    WHERE completed_at IS NULL AND invalidated_at IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_signup_otp_superseded_session'
    ) THEN
        ALTER TABLE signup_otp_sessions
            ADD CONSTRAINT fk_signup_otp_superseded_session
            FOREIGN KEY (superseded_by_session_id)
            REFERENCES signup_otp_sessions(signup_session_id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- Refresh-token family, session, rotation and reuse-detection fields.
ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS token_family_id uuid,
    ADD COLUMN IF NOT EXISTS session_id uuid,
    ADD COLUMN IF NOT EXISTS parent_refresh_token_id uuid,
    ADD COLUMN IF NOT EXISTS replaced_by_refresh_token_id uuid,
    ADD COLUMN IF NOT EXISTS replaced_by_token_hash text,
    ADD COLUMN IF NOT EXISTS device_id_hash text,
    ADD COLUMN IF NOT EXISTS issued_ip inet,
    ADD COLUMN IF NOT EXISTS last_used_ip inet,
    ADD COLUMN IF NOT EXISTS user_agent_hash text,
    ADD COLUMN IF NOT EXISTS last_used_at timestamptz,
    ADD COLUMN IF NOT EXISTS reused_at timestamptz,
    ADD COLUMN IF NOT EXISTS revocation_reason text,
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

UPDATE refresh_tokens
SET token_family_id = gen_random_uuid()
WHERE token_family_id IS NULL;

UPDATE refresh_tokens
SET session_id = gen_random_uuid()
WHERE session_id IS NULL;

ALTER TABLE refresh_tokens
    ALTER COLUMN token_family_id SET NOT NULL,
    ALTER COLUMN session_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family
    ON refresh_tokens (token_family_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_session
    ON refresh_tokens (session_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_active_v2
    ON refresh_tokens (user_id, expires_at)
    WHERE revoked_at IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_refresh_parent_token'
    ) THEN
        ALTER TABLE refresh_tokens
            ADD CONSTRAINT fk_refresh_parent_token
            FOREIGN KEY (parent_refresh_token_id)
            REFERENCES refresh_tokens(refresh_token_id)
            ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_refresh_replacement_token'
    ) THEN
        ALTER TABLE refresh_tokens
            ADD CONSTRAINT fk_refresh_replacement_token
            FOREIGN KEY (replaced_by_refresh_token_id)
            REFERENCES refresh_tokens(refresh_token_id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- Password-reset lifecycle.
CREATE TABLE IF NOT EXISTS password_reset_sessions (
    password_reset_session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    used_at timestamptz,
    invalidated_at timestamptz,
    requested_ip inet,
    completed_ip inet,
    device_id_hash text,
    correlation_id text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_password_reset_user_active
    ON password_reset_sessions (user_id, expires_at)
    WHERE used_at IS NULL AND invalidated_at IS NULL;

-- Immutable authentication audit trail.
CREATE TABLE IF NOT EXISTS auth_audit_events (
    audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type text NOT NULL,
    outcome text NOT NULL,
    user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    actor_user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    identifier_hash text,
    signup_session_id uuid REFERENCES signup_otp_sessions(signup_session_id) ON DELETE SET NULL,
    auth_session_id uuid,
    ip_address inet,
    device_id_hash text,
    user_agent_hash text,
    correlation_id text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_audit_created
    ON auth_audit_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_auth_audit_user
    ON auth_audit_events (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_auth_audit_event
    ON auth_audit_events (event_type, created_at DESC);

-- Public FPO access requests. This does not create a user.
CREATE TABLE IF NOT EXISTS fpo_access_requests (
    request_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_name text NOT NULL,
    registration_number text,
    contact_person_name text NOT NULL,
    contact_email text NOT NULL,
    contact_phone text NOT NULL,
    state_name text,
    district_name text,
    message text,
    status text NOT NULL DEFAULT 'pending',
    reviewed_by uuid REFERENCES users(user_id) ON DELETE SET NULL,
    reviewed_at timestamptz,
    review_note text,
    created_ip inet,
    device_id_hash text,
    correlation_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_access_status
        CHECK (status IN ('pending', 'approved', 'rejected', 'closed'))
);

CREATE INDEX IF NOT EXISTS idx_fpo_access_status_created
    ON fpo_access_requests (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fpo_access_contact_email
    ON fpo_access_requests (lower(contact_email));

-- Admin-created account invitations.
CREATE TABLE IF NOT EXISTS account_invitations (
    invitation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL,
    role text NOT NULL,
    token_hash text NOT NULL UNIQUE,
    invited_by uuid NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    expires_at timestamptz NOT NULL,
    accepted_at timestamptz,
    revoked_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_account_invitation_role
        CHECK (role IN ('admin', 'fpo'))
);

CREATE INDEX IF NOT EXISTS idx_account_invitations_email_active
    ON account_invitations (lower(email), expires_at)
    WHERE accepted_at IS NULL AND revoked_at IS NULL;

-- Convert the existing email table into a real queue while preserving old rows.
ALTER TABLE email_outbox
    ADD COLUMN IF NOT EXISTS payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS encrypted_payload bytea,
    ADD COLUMN IF NOT EXISTS attempts integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz,
    ADD COLUMN IF NOT EXISTS locked_at timestamptz,
    ADD COLUMN IF NOT EXISTS locked_by text,
    ADD COLUMN IF NOT EXISTS provider_request_id text,
    ADD COLUMN IF NOT EXISTS last_error_code text,
    ADD COLUMN IF NOT EXISTS last_error_message text,
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

UPDATE email_outbox
SET status = 'queued'
WHERE status IS NULL OR status IN ('pending', 'created');

UPDATE email_outbox
SET status = 'sending'
WHERE status IN ('processing', 'in_progress');

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM email_outbox
        WHERE status NOT IN ('queued', 'sending', 'sent', 'failed', 'dead')
    ) THEN
        RAISE EXCEPTION 'email_outbox contains unsupported legacy status values. Review them before continuing.';
    END IF;
END $$;

UPDATE email_outbox
SET next_attempt_at = COALESCE(next_attempt_at, created_at, now())
WHERE status IN ('queued', 'failed');

ALTER TABLE email_outbox
    ALTER COLUMN status SET DEFAULT 'queued',
    ALTER COLUMN status SET NOT NULL;

DO $$
DECLARE
    constraint_row record;
BEGIN
    FOR constraint_row IN
        SELECT c.conname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'email_outbox'
          AND c.contype = 'c'
          AND pg_get_constraintdef(c.oid) ILIKE '%status%'
    LOOP
        EXECUTE format('ALTER TABLE email_outbox DROP CONSTRAINT %I', constraint_row.conname);
    END LOOP;
END $$;

ALTER TABLE email_outbox
    ADD CONSTRAINT ck_email_outbox_status
    CHECK (status IN ('queued', 'sending', 'sent', 'failed', 'dead'));

CREATE INDEX IF NOT EXISTS idx_email_outbox_queue
    ON email_outbox (status, next_attempt_at, created_at)
    WHERE status IN ('queued', 'failed');

COMMIT;
