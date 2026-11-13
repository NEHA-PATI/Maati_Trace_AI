BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- FPO-03A to FPO-03D forward-only verification hardening.
ALTER TABLE public.fpo_verification_documents
    ADD COLUMN IF NOT EXISTS document_version integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS declared_mime_type text,
    ADD COLUMN IF NOT EXISTS detected_mime_type text,
    ADD COLUMN IF NOT EXISTS declared_checksum text,
    ADD COLUMN IF NOT EXISTS verified_checksum text,
    ADD COLUMN IF NOT EXISTS storage_provider text NOT NULL DEFAULT 'LOCAL',
    ADD COLUMN IF NOT EXISTS storage_bucket text,
    -- storage_version is an integer in the earlier document lifecycle
    -- migrations and is incremented by the upload-finalization code.
    ADD COLUMN IF NOT EXISTS storage_version integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS scan_error_code text,
    ADD COLUMN IF NOT EXISTS scan_engine text,
    ADD COLUMN IF NOT EXISTS scan_engine_version text,
    ADD COLUMN IF NOT EXISTS scan_signature_version text,
    ADD COLUMN IF NOT EXISTS scan_next_attempt_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS supersedes_document_id uuid REFERENCES public.fpo_verification_documents(document_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS replaced_by_document_id uuid REFERENCES public.fpo_verification_documents(document_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS deletion_status text NOT NULL DEFAULT 'ACTIVE',
    ADD COLUMN IF NOT EXISTS retention_until timestamptz,
    ADD COLUMN IF NOT EXISTS deleted_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS deletion_reason text;

ALTER TABLE public.fpo_verification_submissions
    ADD COLUMN IF NOT EXISTS submission_number text,
    ADD COLUMN IF NOT EXISTS submission_version integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS previous_submission_id uuid REFERENCES public.fpo_verification_submissions(submission_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS profile_id uuid REFERENCES public.fpos(fpo_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS profile_version integer,
    ADD COLUMN IF NOT EXISTS profile_snapshot_hash text,
    ADD COLUMN IF NOT EXISTS required_document_policy_version text,
    ADD COLUMN IF NOT EXISTS checklist_policy_version text NOT NULL DEFAULT 'fpo-verification-v1',
    ADD COLUMN IF NOT EXISTS decision_reason_code text,
    ADD COLUMN IF NOT EXISTS decision_note text,
    ADD COLUMN IF NOT EXISTS submitted_at timestamptz,
    ADD COLUMN IF NOT EXISTS decided_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS decided_at timestamptz;

ALTER TABLE public.fpo_verification_cases
    ADD COLUMN IF NOT EXISTS case_number text,
    ADD COLUMN IF NOT EXISTS assigned_at timestamptz,
    ADD COLUMN IF NOT EXISTS review_started_at timestamptz,
    ADD COLUMN IF NOT EXISTS escalated_at timestamptz,
    ADD COLUMN IF NOT EXISTS closed_at timestamptz,
    ADD COLUMN IF NOT EXISTS risk_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS case_version integer NOT NULL DEFAULT 1;

ALTER TABLE public.fpo_verification_checklist_results
    ADD COLUMN IF NOT EXISTS policy_version text NOT NULL DEFAULT 'fpo-verification-v1',
    ADD COLUMN IF NOT EXISTS reason_code text,
    ADD COLUMN IF NOT EXISTS reviewer_note text,
    ADD COLUMN IF NOT EXISTS evidence_document_id uuid REFERENCES public.fpo_verification_documents(document_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reviewed_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reviewed_at timestamptz;

CREATE TABLE IF NOT EXISTS public.fpo_verification_document_events (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES public.fpo_verification_documents(document_id) ON DELETE RESTRICT,
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    event_type text NOT NULL,
    actor_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_fpo_verification_document_events_document
    ON public.fpo_verification_document_events (document_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_fpo_verification_document_events_fpo
    ON public.fpo_verification_document_events (fpo_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_verification_storage_deletions (
    deletion_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES public.fpo_verification_documents(document_id) ON DELETE RESTRICT,
    object_key text NOT NULL,
    status text NOT NULL DEFAULT 'PENDING',
    attempts integer NOT NULL DEFAULT 0,
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    last_error text,
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_fpo_verification_storage_deletions_queue
    ON public.fpo_verification_storage_deletions (status, next_attempt_at);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_verification_document_version_positive') THEN
        ALTER TABLE public.fpo_verification_documents
            ADD CONSTRAINT ck_fpo_verification_document_version_positive
            CHECK (document_version > 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_verification_document_scan_attempts_nonnegative') THEN
        ALTER TABLE public.fpo_verification_documents
            ADD CONSTRAINT ck_fpo_verification_document_scan_attempts_nonnegative
            CHECK (scan_attempts >= 0 AND scan_max_attempts > 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_verification_submission_version_positive') THEN
        ALTER TABLE public.fpo_verification_submissions
            ADD CONSTRAINT ck_fpo_verification_submission_version_positive
            CHECK (submission_version > 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_verification_case_version_positive') THEN
        ALTER TABLE public.fpo_verification_cases
            ADD CONSTRAINT ck_fpo_verification_case_version_positive
            CHECK (case_version > 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_verification_deletion_status') THEN
        ALTER TABLE public.fpo_verification_documents
            ADD CONSTRAINT ck_fpo_verification_deletion_status
            CHECK (deletion_status IN ('ACTIVE','QUEUED','DELETED','FAILED')) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_verification_storage_deletion_status') THEN
        ALTER TABLE public.fpo_verification_storage_deletions
            ADD CONSTRAINT ck_fpo_verification_storage_deletion_status
            CHECK (status IN ('PENDING','PROCESSING','DELETED','FAILED','DEAD')) NOT VALID;
    END IF;
END $$;

ALTER TABLE public.fpo_verification_submission_documents
    ADD COLUMN IF NOT EXISTS document_version integer NOT NULL DEFAULT 1;

DO $$
BEGIN
    ALTER TABLE public.fpo_verification_submissions DROP CONSTRAINT IF EXISTS ck_fpo_verification_submission_status;
    ALTER TABLE public.fpo_verification_submissions ADD CONSTRAINT ck_fpo_verification_submission_status
        CHECK (status IN ('DRAFT','SUBMITTED','UNDER_REVIEW','CHANGES_REQUIRED','APPROVED','REJECTED','WITHDRAWN','SUPERSEDED','SUSPENDED'));
    ALTER TABLE public.fpo_verification_cases DROP CONSTRAINT IF EXISTS ck_fpo_verification_case_status;
    ALTER TABLE public.fpo_verification_cases ADD CONSTRAINT ck_fpo_verification_case_status
        CHECK (status IN ('OPEN','CLAIMED','UNDER_REVIEW','CHANGES_REQUIRED','APPROVED','REJECTED','CLOSED'));
END $$;

ALTER TABLE public.fpo_required_document_policies
    ADD COLUMN IF NOT EXISTS policy_version text NOT NULL DEFAULT 'fpo-documents-v1',
    ADD COLUMN IF NOT EXISTS display_name text,
    ADD COLUMN IF NOT EXISTS description text,
    ADD COLUMN IF NOT EXISTS accepted_mime_types text[] NOT NULL DEFAULT '{application/pdf,image/jpeg,image/png}',
    ADD COLUMN IF NOT EXISTS maximum_size_bytes bigint NOT NULL DEFAULT 20971520,
    ADD COLUMN IF NOT EXISTS minimum_document_count integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS requires_expiry_date boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS requires_registration_number_match boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS requires_name_match boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS effective_from timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS effective_until timestamptz,
    ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'PUBLISHED',
    ADD COLUMN IF NOT EXISTS created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS published_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS published_at timestamptz;

UPDATE public.fpo_verification_submissions
SET submitted_at = COALESCE(submitted_at, created_at),
    profile_id = COALESCE(profile_id, (SELECT profile_fpo_id FROM public.fpo_organizations o WHERE o.fpo_id = fpo_verification_submissions.fpo_id)),
    submission_number = COALESCE(submission_number, 'FPOVER-' || to_char(created_at, 'YYYY') || '-' || right(replace(submission_id::text, '-', ''), 8)),
    profile_snapshot_hash = COALESCE(profile_snapshot_hash, encode(digest(profile_snapshot::text, 'sha256'), 'hex'));

UPDATE public.fpo_verification_cases
SET case_number = COALESCE(case_number, 'FPOCASE-' || to_char(created_at, 'YYYY') || '-' || right(replace(case_id::text, '-', ''), 8));

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_verification_submission_number
    ON public.fpo_verification_submissions (submission_number)
    WHERE submission_number IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_verification_case_number
    ON public.fpo_verification_cases (case_number)
    WHERE case_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_fpo_verification_scan_queue
    ON public.fpo_verification_documents (scan_status, scan_next_attempt_at, created_at)
    WHERE upload_status = 'AVAILABLE' AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_fpo_verification_document_versions
    ON public.fpo_verification_documents (fpo_id, document_type, document_version DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_fpo_verification_case_assignment
    ON public.fpo_verification_cases (assigned_reviewer_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS ix_fpo_verification_case_sla
    ON public.fpo_verification_cases (status, sla_due_at)
    WHERE status NOT IN ('CLOSED','APPROVED','REJECTED');

COMMIT;
