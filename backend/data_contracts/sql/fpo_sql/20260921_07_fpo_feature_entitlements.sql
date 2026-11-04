BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_feature_catalogue (
    feature_key varchar(100) PRIMARY KEY,
    display_name varchar(160) NOT NULL,
    description text NOT NULL,
    category varchar(80) NOT NULL,
    is_active boolean NOT NULL DEFAULT TRUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_class_feature_versions (
    class_feature_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    class_code varchar(20) NOT NULL,
    version integer NOT NULL,
    feature_key varchar(100) NOT NULL REFERENCES public.fpo_feature_catalogue(feature_key) ON DELETE RESTRICT,
    enabled boolean NOT NULL DEFAULT FALSE,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    published_at timestamptz,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_class_code CHECK (class_code IN ('A', 'B', 'C')),
    CONSTRAINT uq_fpo_class_feature_version UNIQUE (class_code, version, feature_key)
);

CREATE INDEX IF NOT EXISTS idx_fpo_class_feature_published
    ON public.fpo_class_feature_versions (class_code, version, feature_key)
    WHERE published_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.fpo_class_assignments (
    assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    class_code varchar(20) NOT NULL,
    configuration_version integer NOT NULL DEFAULT 1,
    assigned_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    is_active boolean NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_fpo_assignment_class CHECK (class_code IN ('A', 'B', 'C'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_active_class_assignment
    ON public.fpo_class_assignments (fpo_id)
    WHERE is_active = TRUE;

CREATE TABLE IF NOT EXISTS public.fpo_feature_overrides (
    override_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    feature_key varchar(100) NOT NULL REFERENCES public.fpo_feature_catalogue(feature_key) ON DELETE RESTRICT,
    enabled boolean NOT NULL,
    reason text NOT NULL,
    starts_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fpo_feature_override_active
    ON public.fpo_feature_overrides (fpo_id, feature_key, starts_at DESC);

INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category)
VALUES
    ('FARMER_DIRECTORY', 'Farmer directory', 'View farmers with an active consented relationship.', 'CLASS_A'),
    ('FARMER_DETAIL', 'Farmer detail', 'View consented farmer profile details.', 'CLASS_A'),
    ('FARM_MAP', 'Farm map', 'View farms belonging to active FPO relationships.', 'CLASS_A'),
    ('LAND_INTELLIGENCE', 'Land intelligence', 'View delegated land and satellite intelligence.', 'CLASS_A'),
    ('BASIC_ALERTS', 'Basic alerts', 'Receive operational alerts for the FPO portfolio.', 'CLASS_A'),
    ('BASIC_REPORTS', 'Basic reports', 'Generate basic portfolio reports.', 'CLASS_A'),
    ('BULK_FARM_REGISTRATION', 'Bulk farm registration', 'Register member farms in controlled batches.', 'CLASS_A')
ON CONFLICT (feature_key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    updated_at = now();

INSERT INTO public.fpo_class_feature_versions
    (class_code, version, feature_key, enabled, configuration, published_at)
SELECT 'A', 1, feature_key, TRUE, '{}'::jsonb, now()
FROM public.fpo_feature_catalogue
WHERE category = 'CLASS_A'
ON CONFLICT (class_code, version, feature_key) DO NOTHING;

INSERT INTO public.fpo_class_feature_versions
    (class_code, version, feature_key, enabled, configuration, published_at)
SELECT class_code, 1, feature_key, FALSE, '{}'::jsonb, now()
FROM (VALUES ('B'), ('C')) classes(class_code)
CROSS JOIN public.fpo_feature_catalogue
ON CONFLICT (class_code, version, feature_key) DO NOTHING;

COMMIT;
