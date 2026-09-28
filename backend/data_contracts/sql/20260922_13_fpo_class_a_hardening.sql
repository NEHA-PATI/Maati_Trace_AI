BEGIN;

-- Forward-only Class A hardening.  The twelve 20260921 migrations remain immutable.
CREATE TABLE IF NOT EXISTS public.fpo_event_inbox (
    inbox_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    consumer_name text NOT NULL,
    event_id uuid NOT NULL,
    event_type text NOT NULL,
    event_version integer NOT NULL DEFAULT 1,
    subject_id uuid,
    payload_hash text NOT NULL,
    status text NOT NULL DEFAULT 'RECEIVED',
    attempts integer NOT NULL DEFAULT 0,
    available_at timestamptz NOT NULL DEFAULT now(),
    locked_at timestamptz,
    processed_at timestamptz,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_event_inbox_status CHECK (status IN ('RECEIVED','PROCESSING','PROCESSED','FAILED','DEAD')),
    CONSTRAINT uq_fpo_event_inbox_consumer_event UNIQUE (consumer_name, event_id)
);

CREATE TABLE IF NOT EXISTS public.fpo_organization_status_events (
    status_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    status_from jsonb NOT NULL DEFAULT '{}'::jsonb,
    status_to jsonb NOT NULL DEFAULT '{}'::jsonb,
    actor_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    reason text,
    effective_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_farmer_relationship_consents (
    consent_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE RESTRICT,
    policy_code text NOT NULL,
    policy_version text NOT NULL,
    purpose text NOT NULL,
    scopes text[] NOT NULL DEFAULT '{}',
    language_code text NOT NULL DEFAULT 'en',
    capture_channel text NOT NULL,
    consent_content_hash text NOT NULL,
    captured_at timestamptz NOT NULL DEFAULT now(),
    captured_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    revoked_at timestamptz,
    revoked_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    revocation_reason text,
    expires_at timestamptz,
    evidence_metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_fpo_relationship_consent_active
    ON public.fpo_farmer_relationship_consents (relationship_id, captured_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_verification_cases (
    case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    submission_id uuid REFERENCES public.fpo_verification_submissions(submission_id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'OPEN',
    priority text NOT NULL DEFAULT 'NORMAL',
    assigned_reviewer_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    checklist_policy_version text NOT NULL DEFAULT 'class-a-v1',
    sla_due_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_verification_case_status CHECK (status IN ('OPEN','CLAIMED','CHANGES_REQUIRED','APPROVED','REJECTED','CLOSED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_verification_cases_queue
    ON public.fpo_verification_cases (status, priority, created_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_verification_case_events (
    case_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id uuid NOT NULL REFERENCES public.fpo_verification_cases(case_id) ON DELETE CASCADE,
    event_type text NOT NULL,
    actor_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    reason text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_verification_checklist_results (
    checklist_result_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id uuid NOT NULL REFERENCES public.fpo_verification_cases(case_id) ON DELETE CASCADE,
    checklist_key text NOT NULL,
    result text NOT NULL DEFAULT 'PENDING',
    note text,
    checked_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    checked_at timestamptz,
    UNIQUE (case_id, checklist_key),
    CONSTRAINT ck_fpo_checklist_result CHECK (result IN ('PENDING','PASS','FAIL','NOT_APPLICABLE'))
);

ALTER TABLE public.fpo_feature_catalogue
    ADD COLUMN IF NOT EXISTS configuration_schema jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS dependencies text[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS risk_level text NOT NULL DEFAULT 'LOW',
    ADD COLUMN IF NOT EXISTS navigation_key text,
    ADD COLUMN IF NOT EXISTS sort_order integer NOT NULL DEFAULT 100;

ALTER TABLE public.fpo_feature_overrides
    ADD COLUMN IF NOT EXISTS configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'ACTIVE',
    ADD COLUMN IF NOT EXISTS reference_ticket text,
    ADD COLUMN IF NOT EXISTS revoked_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS revoked_at timestamptz,
    ADD COLUMN IF NOT EXISTS revocation_reason text;

ALTER TABLE public.fpo_operational_alerts
    ADD COLUMN IF NOT EXISTS deduplication_key text,
    ADD COLUMN IF NOT EXISTS source_entity_type text,
    ADD COLUMN IF NOT EXISTS source_entity_id uuid,
    ADD COLUMN IF NOT EXISTS deep_link_route text,
    ADD COLUMN IF NOT EXISTS first_observed_at timestamptz,
    ADD COLUMN IF NOT EXISTS last_observed_at timestamptz,
    ADD COLUMN IF NOT EXISTS occurrence_count integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS resolved_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS resolved_at timestamptz,
    ADD COLUMN IF NOT EXISTS resolution_reason text;
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_alert_dedupe_active
    ON public.fpo_operational_alerts (fpo_id, deduplication_key)
    WHERE deduplication_key IS NOT NULL AND status <> 'RESOLVED';

CREATE TABLE IF NOT EXISTS public.fpo_sensitive_access_events (
    access_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    actor_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    farmer_id uuid REFERENCES public.farmer_profiles(farmer_id) ON DELETE SET NULL,
    farm_id uuid,
    operation text NOT NULL,
    scopes text[] NOT NULL DEFAULT '{}',
    correlation_id text,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- PostgreSQL has no ALTER TABLE ... ADD CONSTRAINT IF NOT EXISTS.  Use
-- catalog checks so this forward migration remains safely rerunnable.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class r ON r.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = r.relnamespace
        WHERE c.conname = 'ck_fpo_commercial_status_hardened'
          AND r.relname = 'fpo_organizations'
          AND n.nspname = 'public'
    ) THEN
        ALTER TABLE public.fpo_organizations
            ADD CONSTRAINT ck_fpo_commercial_status_hardened
            CHECK (commercial_status IN ('UNASSIGNED','FREE','TRIAL','PAID','OVERDUE','CANCELLED'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class r ON r.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = r.relnamespace
        WHERE c.conname = 'ck_fpo_profile_percentages'
          AND r.relname = 'fpos'
          AND n.nspname = 'public'
    ) THEN
        ALTER TABLE public.fpos
            ADD CONSTRAINT ck_fpo_profile_percentages
            CHECK (
                profile_completion_percentage BETWEEN 0 AND 100
                AND verification_readiness_percentage BETWEEN 0 AND 100
            );
    END IF;
END $$;

COMMIT;
