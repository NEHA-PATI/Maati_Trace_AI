BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_data_sharing_grants (
    grant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, farmer_id uuid NOT NULL REFERENCES public.farmer_profiles(farmer_id) ON DELETE RESTRICT,
    consent_id uuid NOT NULL REFERENCES public.fpo_farmer_relationship_consents(consent_id) ON DELETE RESTRICT, purpose_code varchar(80) NOT NULL, recipient_category varchar(40) NOT NULL, recipient_id uuid,
    allowed_schema_key varchar(100) NOT NULL, allowed_schema_version integer NOT NULL, allowed_field_paths jsonb NOT NULL DEFAULT '[]'::jsonb, issued_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz,
    revoked_at timestamptz, revocation_reason text, created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, status varchar(20) NOT NULL DEFAULT 'ACTIVE', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_grant_status CHECK (status IN ('ACTIVE','EXPIRED','REVOKED')), CONSTRAINT ck_fpo_grant_dates CHECK (expires_at IS NULL OR expires_at > issued_at)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_active_sharing_grant ON public.fpo_data_sharing_grants (fpo_id,farmer_id,purpose_code,recipient_category,recipient_id,allowed_schema_key,allowed_schema_version) WHERE status='ACTIVE' AND revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS public.fpo_data_pack_schemas (
    data_pack_schema_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), schema_key varchar(100) NOT NULL, version integer NOT NULL DEFAULT 1, name varchar(180) NOT NULL, purpose_code varchar(80) NOT NULL,
    recipient_category varchar(40) NOT NULL, allowed_field_paths jsonb NOT NULL DEFAULT '[]'::jsonb, status varchar(20) NOT NULL DEFAULT 'DRAFT', created_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, published_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, published_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(schema_key,version), CONSTRAINT ck_fpo_data_schema_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_data_pack_requests (
    request_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, schema_id uuid NOT NULL REFERENCES public.fpo_data_pack_schemas(data_pack_schema_id) ON DELETE RESTRICT,
    purpose_code varchar(80) NOT NULL, recipient_category varchar(40) NOT NULL, recipient_id uuid, farmer_ids jsonb NOT NULL DEFAULT '[]'::jsonb, consent_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(25) NOT NULL DEFAULT 'DRAFT', validation_result jsonb NOT NULL DEFAULT '{}'::jsonb, artifact_object_key text, artifact_checksum varchar(128), expires_at timestamptz, revoked_at timestamptz,
    requested_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_data_pack_status CHECK (status IN ('DRAFT','CONSENT_VALIDATED','UNDER_APPROVAL','APPROVED','GENERATING','READY','REVOKED','EXPIRED','FAILED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_sustainability_methodologies (
    methodology_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), metric_code varchar(80) NOT NULL, version integer NOT NULL DEFAULT 1, name varchar(180) NOT NULL, formula text NOT NULL, unit_code varchar(30) NOT NULL, source_reference text NOT NULL, status varchar(20) NOT NULL DEFAULT 'DRAFT', created_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, published_at timestamptz, UNIQUE(metric_code,version), CONSTRAINT ck_fpo_methodology_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_sustainability_metrics (
    metric_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, methodology_id uuid NOT NULL REFERENCES public.fpo_sustainability_methodologies(methodology_id) ON DELETE RESTRICT,
    metric_code varchar(80) NOT NULL, scope_type varchar(30) NOT NULL, scope_reference jsonb NOT NULL DEFAULT '{}'::jsonb, metric_value numeric(18,6) NOT NULL, unit_code varchar(30) NOT NULL, coverage_percent numeric(5,2), data_through timestamptz, calculation_run_id uuid, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_fpo_sustainability_metrics_owner ON public.fpo_sustainability_metrics (fpo_id,metric_code,created_at DESC);

COMMIT;
