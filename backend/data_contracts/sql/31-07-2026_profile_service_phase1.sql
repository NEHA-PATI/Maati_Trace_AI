BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- FARMER PROFILE LOCATION CONTRACT
--
-- Auth signup currently creates a minimal profile using:
-- district_name = 'Pending'
--
-- Keep district_name NOT NULL so the existing working auth flow is unchanged.
-- Profile service treats 'Pending' as logically missing.
-- ============================================================================

UPDATE public.farmer_profiles
SET district_name = 'Pending'
WHERE district_name IS NULL
   OR trim(district_name) = ''
   OR lower(trim(district_name)) IN (
       'pending',
       'unassigned',
       'not assigned',
       'not selected'
   );

ALTER TABLE public.farmer_profiles
    ALTER COLUMN district_name SET DEFAULT 'Pending',
    ALTER COLUMN district_name SET NOT NULL;

-- Optional location columns should use NULL rather than placeholder text.

UPDATE public.farmer_profiles
SET block_name = NULL
WHERE block_name IS NOT NULL
  AND (
      trim(block_name) = ''
      OR lower(trim(block_name)) IN (
          'pending',
          'unassigned',
          'not assigned',
          'not selected'
      )
  );

UPDATE public.farmer_profiles
SET village_name = NULL
WHERE village_name IS NOT NULL
  AND (
      trim(village_name) = ''
      OR lower(trim(village_name)) IN (
          'pending',
          'unassigned',
          'not assigned',
          'not selected'
      )
  );

-- ============================================================================
-- EXTENDED FARMER PROFILE FIELDS
-- ============================================================================

ALTER TABLE public.farmer_profiles
    ADD COLUMN IF NOT EXISTS date_of_birth date,
    ADD COLUMN IF NOT EXISTS preferred_language text NOT NULL DEFAULT 'en',
    ADD COLUMN IF NOT EXISTS aadhaar_last4 text,
    ADD COLUMN IF NOT EXISTS kyc_status text NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS gram_panchayat text,
    ADD COLUMN IF NOT EXISTS pincode text,
    ADD COLUMN IF NOT EXISTS farmer_type text,
    ADD COLUMN IF NOT EXISTS total_landholding_acres numeric(12, 4),
    ADD COLUMN IF NOT EXISTS cultivated_area_acres numeric(12, 4),
    ADD COLUMN IF NOT EXISTS primary_crop text,
    ADD COLUMN IF NOT EXISTS irrigation_status text,

    ADD COLUMN IF NOT EXISTS consent_location_use boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS consent_data_processing boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS consent_advisory_messages boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS consent_fpo_data_sharing boolean NOT NULL DEFAULT false,

    ADD COLUMN IF NOT EXISTS consent_location_use_at timestamptz,
    ADD COLUMN IF NOT EXISTS consent_data_processing_at timestamptz,
    ADD COLUMN IF NOT EXISTS consent_advisory_messages_at timestamptz,
    ADD COLUMN IF NOT EXISTS consent_fpo_data_sharing_at timestamptz,

    ADD COLUMN IF NOT EXISTS profile_image_url text,
    ADD COLUMN IF NOT EXISTS onboarding_completed_at timestamptz,
    ADD COLUMN IF NOT EXISTS profile_version integer NOT NULL DEFAULT 1;

-- ============================================================================
-- EXTENDED FPO PROFILE FIELDS
-- ============================================================================

ALTER TABLE public.fpos
    ADD COLUMN IF NOT EXISTS district_code integer,
    ADD COLUMN IF NOT EXISTS registration_type text,
    ADD COLUMN IF NOT EXISTS date_of_registration date,
    ADD COLUMN IF NOT EXISTS promoted_by text,
    ADD COLUMN IF NOT EXISTS promoting_institution_name text,

    ADD COLUMN IF NOT EXISTS contact_person_name text,
    ADD COLUMN IF NOT EXISTS contact_person_designation text,
    ADD COLUMN IF NOT EXISTS alternate_phone text,

    ADD COLUMN IF NOT EXISTS village_name text,
    ADD COLUMN IF NOT EXISTS gram_panchayat text,
    ADD COLUMN IF NOT EXISTS pincode text,
    ADD COLUMN IF NOT EXISTS office_address text,

    ADD COLUMN IF NOT EXISTS main_commodities text[] NOT NULL
        DEFAULT ARRAY[]::text[],

    ADD COLUMN IF NOT EXISTS member_count integer,
    ADD COLUMN IF NOT EXISTS active_member_count integer,

    ADD COLUMN IF NOT EXISTS services_provided text[] NOT NULL
        DEFAULT ARRAY[]::text[],

    ADD COLUMN IF NOT EXISTS verification_status text NOT NULL
        DEFAULT 'pending',

    ADD COLUMN IF NOT EXISTS profile_image_url text,
    ADD COLUMN IF NOT EXISTS onboarding_completed_at timestamptz,
    ADD COLUMN IF NOT EXISTS profile_version integer NOT NULL DEFAULT 1;

-- ============================================================================
-- FPO ROLE COMPATIBILITY
--
-- Live DB uses fpo_role.
-- Existing farm registry code may still use role.
-- Keep both synchronized during the compatibility period.
-- ============================================================================

ALTER TABLE public.fpo_users
    ADD COLUMN IF NOT EXISTS fpo_role text,
    ADD COLUMN IF NOT EXISTS role text,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

UPDATE public.fpo_users
SET fpo_role = COALESCE(
        NULLIF(trim(fpo_role), ''),
        NULLIF(trim(role), ''),
        'manager'
    ),
    role = COALESCE(
        NULLIF(trim(fpo_role), ''),
        NULLIF(trim(role), ''),
        'manager'
    );

ALTER TABLE public.fpo_users
    ALTER COLUMN fpo_role SET DEFAULT 'manager',
    ALTER COLUMN fpo_role SET NOT NULL,
    ALTER COLUMN role SET DEFAULT 'manager',
    ALTER COLUMN role SET NOT NULL;

CREATE OR REPLACE FUNCTION public.sync_fpo_user_roles()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.fpo_role := COALESCE(
            NULLIF(trim(NEW.fpo_role), ''),
            NULLIF(trim(NEW.role), ''),
            'manager'
        );

        NEW.role := NEW.fpo_role;
        RETURN NEW;
    END IF;

    IF NEW.fpo_role IS DISTINCT FROM OLD.fpo_role
       AND NEW.role IS NOT DISTINCT FROM OLD.role THEN
        NEW.role := NEW.fpo_role;

    ELSIF NEW.role IS DISTINCT FROM OLD.role
       AND NEW.fpo_role IS NOT DISTINCT FROM OLD.fpo_role THEN
        NEW.fpo_role := NEW.role;

    ELSIF NEW.role IS DISTINCT FROM NEW.fpo_role THEN
        RAISE EXCEPTION
            'fpo_role and role must contain the same value';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sync_fpo_user_roles
ON public.fpo_users;

CREATE TRIGGER trg_sync_fpo_user_roles
BEFORE INSERT OR UPDATE OF role, fpo_role
ON public.fpo_users
FOR EACH ROW
EXECUTE FUNCTION public.sync_fpo_user_roles();

-- ============================================================================
-- CANONICAL FARMER LOCATION PLACEHOLDER
--
-- Any missing district is stored as 'Pending'.
-- This preserves the current auth profile-stub implementation.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.canonicalize_farmer_profile_location()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.district_name IS NULL
       OR trim(NEW.district_name) = ''
       OR lower(trim(NEW.district_name)) IN (
           'pending',
           'unassigned',
           'not assigned',
           'not selected'
       ) THEN
        NEW.district_name := 'Pending';
    ELSE
        NEW.district_name := trim(NEW.district_name);
    END IF;

    IF NEW.block_name IS NOT NULL THEN
        IF trim(NEW.block_name) = ''
           OR lower(trim(NEW.block_name)) IN (
               'pending',
               'unassigned',
               'not assigned',
               'not selected'
           ) THEN
            NEW.block_name := NULL;
        ELSE
            NEW.block_name := trim(NEW.block_name);
        END IF;
    END IF;

    IF NEW.village_name IS NOT NULL THEN
        IF trim(NEW.village_name) = ''
           OR lower(trim(NEW.village_name)) IN (
               'pending',
               'unassigned',
               'not assigned',
               'not selected'
           ) THEN
            NEW.village_name := NULL;
        ELSE
            NEW.village_name := trim(NEW.village_name);
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_canonicalize_farmer_profile_location
ON public.farmer_profiles;

CREATE TRIGGER trg_canonicalize_farmer_profile_location
BEFORE INSERT OR UPDATE OF
    district_name,
    block_name,
    village_name
ON public.farmer_profiles
FOR EACH ROW
EXECUTE FUNCTION public.canonicalize_farmer_profile_location();

-- ============================================================================
-- REPAIR FARMER USERS WITHOUT PROFILES
--
-- Auth is not changed.
-- This repairs legacy users and any previous partial data.
-- ============================================================================

INSERT INTO public.farmer_profiles (
    user_id,
    fpo_id,
    full_name,
    phone_number,
    gender,
    state_name,
    district_name,
    district_code,
    block_name,
    block_code,
    village_name,
    is_active,
    created_at,
    updated_at
)
SELECT
    u.user_id,
    NULL,
    u.full_name,
    u.phone_number,
    NULL,
    'Odisha',
    'Pending',
    NULL,
    NULL,
    NULL,
    NULL,
    TRUE,
    now(),
    now()
FROM public.users u
WHERE u.role = 'farmer'
  AND NOT EXISTS (
      SELECT 1
      FROM public.farmer_profiles fp
      WHERE fp.user_id = u.user_id
  );

-- ============================================================================
-- PROFILE AUDIT LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.profile_audit_events (
    profile_audit_event_id uuid PRIMARY KEY
        DEFAULT gen_random_uuid(),

    entity_type text NOT NULL,
    entity_id uuid NOT NULL,

    subject_user_id uuid,
    actor_user_id uuid,

    event_type text NOT NULL,

    changed_fields jsonb NOT NULL
        DEFAULT '{}'::jsonb,

    correlation_id text,
    ip_address inet,

    created_at timestamptz NOT NULL
        DEFAULT now(),

    CONSTRAINT profile_audit_events_subject_user_fkey
        FOREIGN KEY (subject_user_id)
        REFERENCES public.users(user_id)
        ON DELETE SET NULL,

    CONSTRAINT profile_audit_events_actor_user_fkey
        FOREIGN KEY (actor_user_id)
        REFERENCES public.users(user_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_profile_audit_entity
ON public.profile_audit_events (
    entity_type,
    entity_id,
    created_at DESC
);

CREATE INDEX IF NOT EXISTS idx_profile_audit_actor
ON public.profile_audit_events (
    actor_user_id,
    created_at DESC
);

-- ============================================================================
-- DATA CONSTRAINTS
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farmer_profiles_aadhaar_last4_check'
    ) THEN
        ALTER TABLE public.farmer_profiles
        ADD CONSTRAINT farmer_profiles_aadhaar_last4_check
        CHECK (
            aadhaar_last4 IS NULL
            OR aadhaar_last4 ~ '^[0-9]{4}$'
        )
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farmer_profiles_pincode_check'
    ) THEN
        ALTER TABLE public.farmer_profiles
        ADD CONSTRAINT farmer_profiles_pincode_check
        CHECK (
            pincode IS NULL
            OR pincode ~ '^[1-9][0-9]{5}$'
        )
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farmer_profiles_landholding_check'
    ) THEN
        ALTER TABLE public.farmer_profiles
        ADD CONSTRAINT farmer_profiles_landholding_check
        CHECK (
            total_landholding_acres IS NULL
            OR total_landholding_acres >= 0
        )
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farmer_profiles_cultivated_area_check'
    ) THEN
        ALTER TABLE public.farmer_profiles
        ADD CONSTRAINT farmer_profiles_cultivated_area_check
        CHECK (
            cultivated_area_acres IS NULL
            OR (
                cultivated_area_acres >= 0
                AND (
                    total_landholding_acres IS NULL
                    OR cultivated_area_acres
                        <= total_landholding_acres
                )
            )
        )
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fpos_member_counts_check'
    ) THEN
        ALTER TABLE public.fpos
        ADD CONSTRAINT fpos_member_counts_check
        CHECK (
            (member_count IS NULL OR member_count >= 0)
            AND (
                active_member_count IS NULL
                OR active_member_count >= 0
            )
            AND (
                member_count IS NULL
                OR active_member_count IS NULL
                OR active_member_count <= member_count
            )
        )
        NOT VALID;
    END IF;
END;
$$;

-- ============================================================================
-- UPDATED_AT MANAGEMENT
-- ============================================================================

CREATE OR REPLACE FUNCTION public.profile_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_farmer_profiles_updated_at
ON public.farmer_profiles;

CREATE TRIGGER trg_farmer_profiles_updated_at
BEFORE UPDATE
ON public.farmer_profiles
FOR EACH ROW
EXECUTE FUNCTION public.profile_set_updated_at();

DROP TRIGGER IF EXISTS trg_fpos_updated_at
ON public.fpos;

CREATE TRIGGER trg_fpos_updated_at
BEFORE UPDATE
ON public.fpos
FOR EACH ROW
EXECUTE FUNCTION public.profile_set_updated_at();

DROP TRIGGER IF EXISTS trg_fpo_users_updated_at
ON public.fpo_users;

CREATE TRIGGER trg_fpo_users_updated_at
BEFORE UPDATE
ON public.fpo_users
FOR EACH ROW
EXECUTE FUNCTION public.profile_set_updated_at();

-- ============================================================================
-- RECALCULATE FARMER COMPLETION
--
-- 'Pending' is explicitly treated as incomplete.
-- ============================================================================

UPDATE public.farmer_profiles fp
SET onboarding_completed_at = CASE
    WHEN NULLIF(trim(fp.full_name), '') IS NOT NULL
     AND NULLIF(trim(fp.phone_number), '') IS NOT NULL
     AND NULLIF(trim(fp.state_name), '') IS NOT NULL

     AND lower(trim(fp.district_name)) NOT IN (
         '',
         'pending',
         'unassigned',
         'not assigned',
         'not selected'
     )

     AND NULLIF(trim(fp.block_name), '') IS NOT NULL
     AND fp.block_code IS NOT NULL
     AND NULLIF(trim(fp.village_name), '') IS NOT NULL
     AND fp.consent_data_processing IS TRUE

    THEN COALESCE(
        fp.onboarding_completed_at,
        now()
    )
    ELSE NULL
END;

UPDATE public.users u
SET onboarding_status = CASE
        WHEN NULLIF(trim(fp.full_name), '') IS NOT NULL
         AND NULLIF(trim(fp.phone_number), '') IS NOT NULL
         AND NULLIF(trim(fp.state_name), '') IS NOT NULL

         AND lower(trim(fp.district_name)) NOT IN (
             '',
             'pending',
             'unassigned',
             'not assigned',
             'not selected'
         )

         AND NULLIF(trim(fp.block_name), '') IS NOT NULL
         AND fp.block_code IS NOT NULL
         AND NULLIF(trim(fp.village_name), '') IS NOT NULL
         AND fp.consent_data_processing IS TRUE

        THEN 'completed'
        ELSE 'pending'
    END,
    updated_at = now()
FROM public.farmer_profiles fp
WHERE u.role = 'farmer'
  AND fp.user_id = u.user_id;

COMMIT;