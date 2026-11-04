BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_verification_submissions (
    submission_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    submitted_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    status varchar(40) NOT NULL DEFAULT 'SUBMITTED',
    profile_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    reviewer_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    reviewer_note text,
    reviewed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_verification_submission_status
        CHECK (status IN ('SUBMITTED', 'UNDER_REVIEW', 'CHANGES_REQUIRED', 'APPROVED', 'REJECTED', 'SUSPENDED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_one_open_verification_submission
    ON public.fpo_verification_submissions (fpo_id)
    WHERE status IN ('SUBMITTED', 'UNDER_REVIEW');

CREATE INDEX IF NOT EXISTS idx_fpo_verification_submissions_review
    ON public.fpo_verification_submissions (status, created_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_verification_documents (
    document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    submission_id uuid REFERENCES public.fpo_verification_submissions(submission_id) ON DELETE SET NULL,
    document_type varchar(80) NOT NULL,
    object_key text NOT NULL,
    original_filename text NOT NULL,
    mime_type varchar(120) NOT NULL,
    size_bytes bigint NOT NULL,
    checksum text NOT NULL,
    uploaded_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_verification_document_size CHECK (size_bytes > 0 AND size_bytes <= 20971520)
);

CREATE INDEX IF NOT EXISTS idx_fpo_verification_documents_fpo
    ON public.fpo_verification_documents (fpo_id, created_at DESC);

COMMIT;
