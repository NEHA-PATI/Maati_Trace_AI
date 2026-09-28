BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_plan_versions (
    plan_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    class_code varchar(20) NOT NULL,
    version integer NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'DRAFT',
    name varchar(160) NOT NULL,
    description text NOT NULL DEFAULT '',
    effective_from timestamptz,
    effective_until timestamptz,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    published_at timestamptz,
    publication_reason text,
    UNIQUE (class_code, version),
    CONSTRAINT ck_fpo_plan_class CHECK (class_code IN ('A','B','C')),
    CONSTRAINT ck_fpo_plan_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED'))
);

-- Version 2 corrects inheritance: B includes A and C includes A+B.
INSERT INTO public.fpo_feature_catalogue (feature_key, display_name, description, category, navigation_key, sort_order)
VALUES
 ('FPO_PROFILE_MANAGEMENT','FPO profile management','Manage the organization profile and verification readiness.','CLASS_A','profile',10),
 ('FPO_PUBLIC_ID','Public FPO ID','View and share the immutable public FPO identifier.','CLASS_A','profile',20),
 ('PORTFOLIO_OVERVIEW','Portfolio overview','View server-maintained portfolio KPIs.','CLASS_A','overview',30),
 ('RELATIONSHIP_INBOX','Relationship inbox','Review consent-backed farmer requests.','CLASS_A','relationships',40),
 ('FARMER_DIRECTORY','Farmer directory','View active consented farmer relationships.','CLASS_A','farmers',50),
 ('FARMER_DETAIL','Farmer detail','View a consent-aware read-only farmer profile.','CLASS_A','farmers',60),
 ('FARM_PORTFOLIO_READ','Farm portfolio','View farms attached to active relationships.','CLASS_A','farms',70),
 ('FARM_MAP','Farm map','View the FPO farm portfolio map.','CLASS_A','farms',80),
 ('LAND_INTELLIGENCE_BASIC','Basic land intelligence','View permitted land intelligence.','CLASS_A','monitoring',90),
 ('CROP_PORTFOLIO_BASIC','Basic crop portfolio','View crop and season portfolio summaries.','CLASS_A','crops',100),
 ('COVERAGE_ANALYTICS_BASIC','Basic coverage','View district and block coverage counts.','CLASS_A','coverage',110),
 ('BASIC_ALERTS','Basic alerts','Acknowledge operational alerts.','CLASS_A','alerts',120),
 ('BASIC_REPORTS','Basic reports','Generate fixed portfolio reports.','CLASS_A','reports',130),
 ('ACTIVITY_FEED','Activity feed','View recent portfolio activity.','CLASS_A','overview',140),
 ('BULK_FARM_REGISTRATION','Bulk farm registration','Register farms in controlled batches.','CLASS_B','farms',200)
ON CONFLICT (feature_key) DO UPDATE SET navigation_key=EXCLUDED.navigation_key, sort_order=EXCLUDED.sort_order;

INSERT INTO public.fpo_plan_versions (class_code, version, status, name, description, effective_from, published_at, publication_reason)
VALUES ('A',2,'PUBLISHED','Foundation v2','Class A foundation plan',now(),now(),'Corrected Class A entitlement baseline'),
       ('B',2,'PUBLISHED','Growth v2','Class A plus Growth capabilities',now(),now(),'Class inheritance correction'),
       ('C',2,'PUBLISHED','Enterprise v2','Class A plus Growth and Enterprise capabilities',now(),now(),'Class inheritance correction')
ON CONFLICT (class_code, version) DO NOTHING;

INSERT INTO public.fpo_class_feature_versions (class_code, version, feature_key, enabled, configuration, published_at)
SELECT c.class_code, 2, f.feature_key,
       CASE WHEN c.class_code='A' THEN f.category='CLASS_A'
            WHEN c.class_code='B' THEN f.category IN ('CLASS_A','CLASS_B')
            ELSE f.category IN ('CLASS_A','CLASS_B','CLASS_C') END,
       '{}'::jsonb, now()
FROM (VALUES ('A'),('B'),('C')) c(class_code)
CROSS JOIN public.fpo_feature_catalogue f
WHERE f.is_active = TRUE
ON CONFLICT (class_code, version, feature_key) DO NOTHING;

-- Bulk registration is deliberately not part of the default Class A plan.
UPDATE public.fpo_class_feature_versions
SET enabled = FALSE
WHERE class_code = 'A' AND version = 2 AND feature_key = 'BULK_FARM_REGISTRATION';
UPDATE public.fpo_class_feature_versions
SET enabled = TRUE
WHERE class_code IN ('B','C') AND version = 2 AND feature_key = 'BULK_FARM_REGISTRATION';

COMMIT;
