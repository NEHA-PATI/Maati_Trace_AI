BEGIN;

ALTER TABLE public.fpo_verification_documents
    ADD COLUMN IF NOT EXISTS upload_status text NOT NULL DEFAULT 'AVAILABLE',
    ADD COLUMN IF NOT EXISTS scan_status text NOT NULL DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS validation_status text NOT NULL DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS validated_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS validated_at timestamptz,
    ADD COLUMN IF NOT EXISTS validation_reason text,
    ADD COLUMN IF NOT EXISTS storage_version integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS deleted_at timestamptz,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_document_upload_status') THEN
        ALTER TABLE public.fpo_verification_documents ADD CONSTRAINT ck_fpo_document_upload_status
            CHECK (upload_status IN ('UPLOADING','AVAILABLE','FAILED','DELETED'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_document_scan_status') THEN
        ALTER TABLE public.fpo_verification_documents ADD CONSTRAINT ck_fpo_document_scan_status
            CHECK (scan_status IN ('PENDING','CLEAN','INFECTED','FAILED'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_document_validation_status') THEN
        ALTER TABLE public.fpo_verification_documents ADD CONSTRAINT ck_fpo_document_validation_status
            CHECK (validation_status IN ('PENDING','VALID','INVALID'));
    END IF;
END $$;

ALTER TABLE public.fpo_farmer_relationship_events
    DROP CONSTRAINT IF EXISTS ck_fpo_farmer_relationship_event_type;
ALTER TABLE public.fpo_farmer_relationship_events
    ADD CONSTRAINT ck_fpo_farmer_relationship_event_type CHECK (
        event_type IN (
            'REQUESTED','CONSENT_RECORDED','ACCEPTED','REJECTED','REVOKED',
            'REQUEST_CANCELLED','TERMINATED_BY_FPO','CONSENT_REVOKED',
            'CONSENT_RENEWED','RELATIONSHIP_EXPIRED','LEGACY_CONSENT_COMPLETED'
        )
    );

CREATE INDEX IF NOT EXISTS idx_fpo_documents_submission_state
    ON public.fpo_verification_documents (submission_id, upload_status, scan_status, validation_status);

COMMIT;
