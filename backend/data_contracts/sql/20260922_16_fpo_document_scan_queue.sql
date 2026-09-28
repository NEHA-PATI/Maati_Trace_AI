BEGIN;

ALTER TABLE public.fpo_verification_documents
    ADD COLUMN IF NOT EXISTS scan_attempts integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS scan_next_attempt_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS scan_error text,
    ADD COLUMN IF NOT EXISTS scanned_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_fpo_document_scan_queue
    ON public.fpo_verification_documents (scan_status, scan_next_attempt_at, created_at)
    WHERE upload_status = 'AVAILABLE' AND deleted_at IS NULL;

COMMIT;
