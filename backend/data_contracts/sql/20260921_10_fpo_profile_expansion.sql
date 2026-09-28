BEGIN;

-- Profile Service remains the owner of these fields; this migration only
-- expands its existing public.fpos contract for the FPO portal.
ALTER TABLE public.fpos
    ADD COLUMN IF NOT EXISTS legal_name text,
    ADD COLUMN IF NOT EXISTS display_name text,
    ADD COLUMN IF NOT EXISTS organisation_type text,
    ADD COLUMN IF NOT EXISTS cin text,
    ADD COLUMN IF NOT EXISTS pan_encrypted bytea,
    ADD COLUMN IF NOT EXISTS gstin text,
    ADD COLUMN IF NOT EXISTS website_url text,
    ADD COLUMN IF NOT EXISTS organisation_description text,
    ADD COLUMN IF NOT EXISTS operating_since_year integer,
    ADD COLUMN IF NOT EXISTS logo_object_key text,
    ADD COLUMN IF NOT EXISTS logo_mime_type text,
    ADD COLUMN IF NOT EXISTS logo_size_bytes integer,
    ADD COLUMN IF NOT EXISTS logo_checksum text,
    ADD COLUMN IF NOT EXISTS registered_address_line_1 text,
    ADD COLUMN IF NOT EXISTS registered_address_line_2 text,
    ADD COLUMN IF NOT EXISTS women_member_count integer,
    ADD COLUMN IF NOT EXISTS small_marginal_member_count integer,
    ADD COLUMN IF NOT EXISTS declared_area_acres numeric(14,4),
    ADD COLUMN IF NOT EXISTS profile_completion_percentage integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS verification_readiness_percentage integer NOT NULL DEFAULT 0;

UPDATE public.fpos
SET legal_name = COALESCE(legal_name, fpo_name),
    display_name = COALESCE(display_name, fpo_name)
WHERE legal_name IS NULL OR display_name IS NULL;

CREATE TABLE IF NOT EXISTS public.fpo_profile_commodities (
    fpo_id uuid NOT NULL REFERENCES public.fpos(fpo_id) ON DELETE CASCADE,
    commodity_code text NOT NULL,
    priority text NOT NULL DEFAULT 'PRIMARY',
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (fpo_id, commodity_code),
    CONSTRAINT ck_fpo_commodity_priority CHECK (priority IN ('PRIMARY', 'SECONDARY'))
);

CREATE TABLE IF NOT EXISTS public.fpo_profile_service_areas (
    service_area_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpos(fpo_id) ON DELETE CASCADE,
    state_code integer NOT NULL,
    district_code integer,
    block_code integer,
    village_code text,
    is_primary boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_profile_services (
    fpo_id uuid NOT NULL REFERENCES public.fpos(fpo_id) ON DELETE CASCADE,
    service_code text NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (fpo_id, service_code)
);

COMMIT;
