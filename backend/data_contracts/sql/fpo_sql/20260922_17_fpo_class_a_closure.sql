BEGIN;

-- Class A closure: server-owned consent, immutable submission evidence,
-- document scan lifecycle, and projection refresh coordination.
CREATE TABLE IF NOT EXISTS public.fpo_consent_scope_catalogue (
    scope_code text PRIMARY KEY,
    display_name text NOT NULL,
    description text NOT NULL,
    is_mandatory boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_consent_policies (
    policy_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_code text NOT NULL,
    version text NOT NULL,
    status text NOT NULL DEFAULT 'DRAFT',
    language_code text NOT NULL DEFAULT 'en',
    title text NOT NULL,
    content text NOT NULL,
    content_hash text NOT NULL,
    mandatory_scopes text[] NOT NULL DEFAULT '{}',
    optional_scopes text[] NOT NULL DEFAULT '{}',
    effective_from timestamptz,
    effective_until timestamptz,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_consent_policy_version UNIQUE (policy_code, version),
    CONSTRAINT ck_fpo_consent_policy_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED'))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_current_consent_policy
    ON public.fpo_consent_policies (policy_code, language_code)
    WHERE status = 'PUBLISHED' AND effective_until IS NULL;

INSERT INTO public.fpo_consent_scope_catalogue (scope_code, display_name, description, is_mandatory)
VALUES
 ('PROFILE_READ','Farmer profile','Read the consented farmer profile.',true),
 ('CONTACT_MASKED_READ','Masked contact','Read a masked phone number.',true),
 ('FARM_READ','Farm records','Read farms owned by the farmer.',true),
 ('CROP_READ','Crop portfolio','Read crop and crop-cycle information.',true),
 ('OBSERVATION_READ','Observations','Read consented crop observations.',true),
 ('LAND_INTELLIGENCE_READ','Land intelligence','Read delegated land intelligence.',true),
 ('ADVISORY_MESSAGE','Advisory messages','Send approved advisory messages.',false),
 ('CONTACT_DIRECT_READ','Direct contact','Read direct contact details.',false),
 ('COMMERCIAL_PARTICIPATION','Commercial participation','Use data for commercial workflows.',false)
ON CONFLICT (scope_code) DO UPDATE SET display_name = EXCLUDED.display_name, description = EXCLUDED.description, is_mandatory = EXCLUDED.is_mandatory;

INSERT INTO public.fpo_consent_policies
    (policy_code, version, status, language_code, title, content, content_hash, mandatory_scopes, optional_scopes, effective_from)
VALUES (
 'FPO_DATA_SHARING', '2', 'PUBLISHED', 'en', 'FPO portfolio data sharing consent',
 'I consent to the selected FPO accessing my permitted farmer, farm, crop, observation and land-intelligence information for the stated purpose. I can revoke this consent at any time.',
 encode(digest('I consent to the selected FPO accessing my permitted farmer, farm, crop, observation and land-intelligence information for the stated purpose. I can revoke this consent at any time.', 'sha256'), 'hex'),
 ARRAY['PROFILE_READ','CONTACT_MASKED_READ','FARM_READ','CROP_READ','OBSERVATION_READ','LAND_INTELLIGENCE_READ'],
 ARRAY['ADVISORY_MESSAGE','CONTACT_DIRECT_READ','COMMERCIAL_PARTICIPATION'], now()
)
ON CONFLICT (policy_code, version) DO UPDATE SET status = EXCLUDED.status, content = EXCLUDED.content, content_hash = EXCLUDED.content_hash, mandatory_scopes = EXCLUDED.mandatory_scopes, optional_scopes = EXCLUDED.optional_scopes, effective_from = EXCLUDED.effective_from;

CREATE TABLE IF NOT EXISTS public.fpo_verification_submission_documents (
    submission_id uuid NOT NULL REFERENCES public.fpo_verification_submissions(submission_id) ON DELETE CASCADE,
    document_id uuid NOT NULL REFERENCES public.fpo_verification_documents(document_id) ON DELETE RESTRICT,
    storage_version integer NOT NULL,
    checksum text NOT NULL,
    linked_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (submission_id, document_id)
);

ALTER TABLE public.fpo_verification_documents
    ADD COLUMN IF NOT EXISTS verified_checksum text,
    ADD COLUMN IF NOT EXISTS scan_locked_at timestamptz,
    ADD COLUMN IF NOT EXISTS scan_worker_id text,
    ADD COLUMN IF NOT EXISTS scan_lease_expires_at timestamptz,
    ADD COLUMN IF NOT EXISTS scan_max_attempts integer NOT NULL DEFAULT 5;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_fpo_document_scan_status') THEN
        ALTER TABLE public.fpo_verification_documents DROP CONSTRAINT ck_fpo_document_scan_status;
    END IF;
    ALTER TABLE public.fpo_verification_documents ADD CONSTRAINT ck_fpo_document_scan_status
        CHECK (scan_status IN ('PENDING','QUEUED','SCANNING','CLEAN','NOT_REQUIRED','INFECTED','QUARANTINED','RETRY','FAILED','DEAD'));
END $$;

CREATE TABLE IF NOT EXISTS public.fpo_required_document_policies (
    registration_type text NOT NULL,
    document_type text NOT NULL,
    is_required boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (registration_type, document_type)
);
INSERT INTO public.fpo_required_document_policies (registration_type, document_type)
VALUES ('DEFAULT','REGISTRATION_CERTIFICATE'), ('DEFAULT','AUTHORIZED_REPRESENTATIVE_DECLARATION'), ('DEFAULT','ADDRESS_PROOF')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS public.fpo_projection_refresh_queue (
    queue_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    event_id uuid,
    event_type text NOT NULL,
    subject_id uuid,
    status text NOT NULL DEFAULT 'QUEUED',
    attempts integer NOT NULL DEFAULT 0,
    available_at timestamptz NOT NULL DEFAULT now(),
    locked_at timestamptz,
    processed_at timestamptz,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_projection_queue_status CHECK (status IN ('QUEUED','PROCESSING','PROCESSED','FAILED','DEAD'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_projection_refresh_queue
    ON public.fpo_projection_refresh_queue (status, available_at, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_one_open_or_active_relationship
    ON public.fpo_farmer_relationships (farmer_user_id)
    WHERE relationship_type = 'PRIMARY' AND status IN ('PENDING_FPO_ACCEPTANCE','ACTIVE');
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_one_current_consent
    ON public.fpo_farmer_relationship_consents (relationship_id)
    WHERE revoked_at IS NULL;

UPDATE public.fpo_feature_catalogue
SET category = 'CLASS_B', updated_at = now()
WHERE feature_key = 'BULK_FARM_REGISTRATION';
UPDATE public.fpo_feature_catalogue
SET is_active = false, updated_at = now()
WHERE feature_key = 'LAND_INTELLIGENCE';

COMMIT;
