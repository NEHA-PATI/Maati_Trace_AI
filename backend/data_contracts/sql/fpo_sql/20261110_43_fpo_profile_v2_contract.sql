-- FPO-02B/C: normalized profile contract, readiness persistence and audit support.
-- Forward-only. Legacy array columns remain for compatibility during migration.
BEGIN;

ALTER TABLE public.fpos
    ADD COLUMN IF NOT EXISTS registration_authority text,
    ADD COLUMN IF NOT EXISTS pan_masked text,
    ADD COLUMN IF NOT EXISTS representative_designation text,
    ADD COLUMN IF NOT EXISTS preferred_language text,
    ADD COLUMN IF NOT EXISTS address_line_1 text,
    ADD COLUMN IF NOT EXISTS address_line_2 text,
    ADD COLUMN IF NOT EXISTS state_code integer,
    ADD COLUMN IF NOT EXISTS village_code text,
    ADD COLUMN IF NOT EXISTS gram_panchayat_code text,
    ADD COLUMN IF NOT EXISTS gram_panchayat_name text,
    ADD COLUMN IF NOT EXISTS postal_code text,
    ADD COLUMN IF NOT EXISTS year_established integer,
    ADD COLUMN IF NOT EXISTS female_member_count integer,
    ADD COLUMN IF NOT EXISTS profile_status text NOT NULL DEFAULT 'DRAFT',
    ADD COLUMN IF NOT EXISTS completion_calculation_version text NOT NULL DEFAULT 'fpo-profile-v2',
    ADD COLUMN IF NOT EXISTS readiness_calculation_version text NOT NULL DEFAULT 'fpo-profile-readiness-v2',
    ADD COLUMN IF NOT EXISTS completion_calculated_at timestamptz,
    ADD COLUMN IF NOT EXISTS readiness_calculated_at timestamptz,
    ADD COLUMN IF NOT EXISTS verification_refresh_required boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS registration_number_normalized text;

UPDATE public.fpos
SET registration_number_normalized = NULLIF(upper(regexp_replace(trim(registration_number), '[^A-Za-z0-9]', '', 'g')), '')
WHERE registration_number_normalized IS NULL AND registration_number IS NOT NULL;

ALTER TABLE public.fpo_profile_commodities
    ADD COLUMN IF NOT EXISTS variety_code text,
    ADD COLUMN IF NOT EXISTS is_primary boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS declared_farmer_count integer,
    ADD COLUMN IF NOT EXISTS declared_area_acres numeric(14,4),
    ADD COLUMN IF NOT EXISTS season_codes text[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'ACTIVE',
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.fpo_profile_services
    ADD COLUMN IF NOT EXISTS display_name text,
    ADD COLUMN IF NOT EXISTS description text,
    ADD COLUMN IF NOT EXISTS active_from date,
    ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'ACTIVE',
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.fpo_profile_service_areas
    ADD COLUMN IF NOT EXISTS geography_level text NOT NULL DEFAULT 'DISTRICT',
    ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'ACTIVE';

CREATE TABLE IF NOT EXISTS public.fpo_profile_events (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type text NOT NULL,
    event_version integer NOT NULL DEFAULT 2,
    profile_id uuid NOT NULL REFERENCES public.fpos(fpo_id) ON DELETE CASCADE,
    organization_id uuid REFERENCES public.fpo_organizations(fpo_id) ON DELETE SET NULL,
    actor_user_id uuid,
    correlation_id text,
    profile_version integer NOT NULL,
    changed_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_profile_change_history (
    history_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id uuid NOT NULL REFERENCES public.fpos(fpo_id) ON DELETE CASCADE,
    actor_user_id uuid,
    previous_profile_version integer NOT NULL,
    new_profile_version integer NOT NULL,
    changed_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
    change_classification text NOT NULL,
    correlation_id text,
    request_channel text NOT NULL DEFAULT 'API',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fpo_profile_events_profile_created
    ON public.fpo_profile_events (profile_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_fpo_profile_history_profile_created
    ON public.fpo_profile_change_history (profile_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_fpo_profile_commodities_active
    ON public.fpo_profile_commodities (fpo_id, status);
CREATE INDEX IF NOT EXISTS ix_fpo_profile_services_active
    ON public.fpo_profile_services (fpo_id, status);
CREATE INDEX IF NOT EXISTS ix_fpo_profile_service_areas_active
    ON public.fpo_profile_service_areas (fpo_id, status);

COMMIT;
