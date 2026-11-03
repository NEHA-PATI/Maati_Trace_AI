BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_compliance_requirements (
    requirement_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), requirement_code varchar(80) NOT NULL, name varchar(180) NOT NULL,
    country_code char(2) NOT NULL, commodity_code varchar(50), activity_code varchar(50), destination_code varchar(50), mandatory boolean NOT NULL DEFAULT true,
    lead_time_days integer NOT NULL DEFAULT 30, definition_json jsonb NOT NULL DEFAULT '{}'::jsonb, status varchar(20) NOT NULL DEFAULT 'DRAFT', version integer NOT NULL DEFAULT 1,
    created_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, published_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE (requirement_code,version), CONSTRAINT ck_fpo_requirement_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_certifications (
    certification_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    certification_code varchar(60) NOT NULL, certification_type_code varchar(60) NOT NULL, certificate_number_encrypted text, issuing_authority varchar(200) NOT NULL,
    scope_type varchar(30) NOT NULL, scope_reference_ids jsonb NOT NULL DEFAULT '{}'::jsonb, issued_date date NOT NULL, effective_date date NOT NULL, expiry_date date,
    verification_url varchar(500), document_artifact_id uuid, document_checksum varchar(128), verification_status varchar(25) NOT NULL DEFAULT 'PENDING', verified_at timestamptz,
    status varchar(25) NOT NULL DEFAULT 'ACTIVE', created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_certification_code UNIQUE (fpo_id,certification_code), CONSTRAINT ck_fpo_certification_status CHECK (status IN ('ACTIVE','EXPIRED','REVOKED','ARCHIVED')), CONSTRAINT ck_fpo_certification_verification CHECK (verification_status IN ('PENDING','UNDER_REVIEW','VERIFIED','REJECTED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_compliance_documents (
    compliance_document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    document_type_code varchar(60) NOT NULL, document_number_encrypted text, issuing_authority varchar(200), issued_date date, expiry_date date, country_code char(2), artifact_id uuid, checksum varchar(128),
    review_status varchar(25) NOT NULL DEFAULT 'PENDING', reviewed_at timestamptz, review_notes text, status varchar(25) NOT NULL DEFAULT 'ACTIVE', created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_compliance_doc_review CHECK (review_status IN ('PENDING','UNDER_REVIEW','APPROVED','REJECTED','EXPIRED')), CONSTRAINT ck_fpo_compliance_doc_status CHECK (status IN ('ACTIVE','EXPIRED','REVOKED','ARCHIVED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_compliance_documents_expiry ON public.fpo_compliance_documents (fpo_id,expiry_date,review_status);

CREATE TABLE IF NOT EXISTS public.fpo_export_packs (
    export_pack_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, pack_code varchar(80) NOT NULL,
    destination_code varchar(50) NOT NULL, commodity_code varchar(50) NOT NULL, order_id uuid REFERENCES public.fpo_orders(order_id) ON DELETE SET NULL, lot_id uuid REFERENCES public.fpo_aggregation_lots(lot_id) ON DELETE SET NULL,
    template_key varchar(100) NOT NULL, template_version integer NOT NULL DEFAULT 1, status varchar(25) NOT NULL DEFAULT 'DRAFT', artifact_id uuid, object_key text, checksum varchar(128), expires_at timestamptz,
    requested_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_export_pack_code UNIQUE (fpo_id,pack_code), CONSTRAINT ck_fpo_export_pack_status CHECK (status IN ('DRAFT','VALIDATING','READY','EXPIRED','REVOKED','FAILED'))
);

COMMIT;
