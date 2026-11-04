BEGIN;

-- Class B v3 is additive and immutable. Class A v2 rows are not modified.
INSERT INTO public.fpo_feature_catalogue
    (feature_key, display_name, description, category, configuration_schema,
     dependencies, risk_level, navigation_key, sort_order)
VALUES
 ('BULK_FARM_REGISTRATION','Bulk onboarding','Upload farmers and farms through dry-run-first controlled imports.','CLASS_B',
  '{"type":"object","required":["max_rows_per_job","require_dry_run","allowed_formats"]}'::jsonb,
  ARRAY['FARMER_DIRECTORY','FARM_PORTFOLIO_READ'],'HIGH','imports',150),
 ('ADVANCED_DIRECTORY_FILTERS','Advanced farmer filters','Filter the consented farmer portfolio by operational attributes.','CLASS_B','{}','{FARMER_DIRECTORY}','LOW','farmers',160),
 ('FARMER_SEGMENTATION','Farmer segments','Create governed dynamic and static farmer segments.','CLASS_B','{}','{FARMER_DIRECTORY}','MEDIUM','segments',170),
 ('FARMER_NOTES_AND_FOLLOWUPS','Farmer notes and follow-ups','Keep private operational notes and follow-ups for the FPO owner.','CLASS_B','{}','{FARMER_DETAIL}','HIGH','farmers',180),
 ('PORTFOLIO_TRENDS','Portfolio trends','View time-series portfolio trends.','CLASS_B','{}','{PORTFOLIO_OVERVIEW}','LOW','overview',190),
 ('COHORT_COMPARISON','Cohort comparison','Compare governed farmer cohorts.','CLASS_B','{}','{FARMER_SEGMENTATION}','MEDIUM','analytics',200),
 ('CROP_PORTFOLIO_ADVANCED','Advanced crop portfolio','View advanced crop portfolio summaries.','CLASS_B','{}','{CROP_PORTFOLIO_BASIC}','MEDIUM','crops',210),
 ('SEASON_PLANNING','Season planning','Plan season crop targets without mutating farmer crop cycles.','CLASS_B','{}','{CROP_PORTFOLIO_ADVANCED}','MEDIUM','seasons',220),
 ('LAND_INTELLIGENCE_COMPARE','Land intelligence comparison','Compare delegated land intelligence observations.','CLASS_B','{}','{LAND_INTELLIGENCE_BASIC}','MEDIUM','monitoring',230),
 ('PORTFOLIO_MONITORING_ADVANCED','Advanced monitoring','Operate governed portfolio monitoring queues.','CLASS_B','{}','{BASIC_ALERTS,FARM_MAP}','MEDIUM','monitoring',240),
 ('ALERT_RULE_MANAGEMENT','Alert rule management','Create versioned metric-backed alert rules.','CLASS_B','{}','{PORTFOLIO_MONITORING_ADVANCED}','HIGH','monitoring',250),
 ('FIELD_ACTIVITY_PLANNING','Tasks and field follow-ups','Plan and track FPO owner field work.','CLASS_B','{}','{FARMER_DETAIL}','MEDIUM','tasks',260),
 ('ADVISORY_WORKBENCH','Advisory workbench','Compose approved agronomy advisories.','CLASS_B','{}','{CROP_PORTFOLIO_ADVANCED}','HIGH','advisories',270),
 ('COMMUNICATION_BROADCAST','Farmer communication campaigns','Plan consent-aware farmer campaigns.','CLASS_B','{}','{ADVISORY_WORKBENCH}','HIGH','advisories',280),
 ('NUTRIENT_PLANNING','Nutrient planning','Use approved nutrient recommendations.','CLASS_B','{}','{ADVISORY_WORKBENCH}','HIGH','advisories',290),
 ('CROP_PROTECTION_MONITORING','Crop protection planning','Use approved crop-protection recommendations.','CLASS_B','{}','{ADVISORY_WORKBENCH}','HIGH','advisories',300),
 ('INPUT_REQUIREMENT_PLANNING','Input demand planning','Aggregate governed season input requirements.','CLASS_B','{}','{SEASON_PLANNING}','MEDIUM','inputs',310),
 ('YIELD_FORECASTS_STANDARD','Standard yield forecasts','View versioned standard yield forecasts.','CLASS_B','{}','{CROP_PORTFOLIO_ADVANCED}','MEDIUM','forecasts',320),
 ('ADVANCED_REPORTS','Advanced reports','Generate governed operational reports.','CLASS_B','{}','{BASIC_REPORTS}','MEDIUM','reports',330),
 ('DATA_EXPORT','Data export','Export governed FPO data asynchronously.','CLASS_B','{}','{ADVANCED_REPORTS}','HIGH','reports',340),
 ('DATA_QUALITY_WORKBENCH','Data quality workbench','Review and resolve portfolio data-quality issues.','CLASS_B','{}','{PORTFOLIO_OVERVIEW}','MEDIUM','data-quality',350)
ON CONFLICT (feature_key) DO UPDATE SET
 display_name=EXCLUDED.display_name, description=EXCLUDED.description, category='CLASS_B',
 configuration_schema=EXCLUDED.configuration_schema, dependencies=EXCLUDED.dependencies,
 risk_level=EXCLUDED.risk_level, navigation_key=EXCLUDED.navigation_key,
 sort_order=EXCLUDED.sort_order, updated_at=now();

INSERT INTO public.fpo_plan_versions
    (class_code, version, status, name, description, effective_from, published_at, publication_reason)
VALUES ('B',3,'PUBLISHED','Growth Operations v3','Class A inheritance plus controlled Class B operations.',now(),now(),'Initial Class B foundation and bulk onboarding release')
ON CONFLICT (class_code, version) DO NOTHING;

INSERT INTO public.fpo_class_feature_versions
    (class_code, version, feature_key, enabled, configuration, published_at)
SELECT 'B', 3, c.feature_key, TRUE,
       CASE c.feature_key
         WHEN 'BULK_FARM_REGISTRATION' THEN '{"max_rows_per_job":5000,"max_jobs_per_day":10,"allowed_formats":["CSV","XLSX"],"require_dry_run":true,"artifact_retention_days":30}'::jsonb
         ELSE '{}'::jsonb
       END, now()
FROM public.fpo_feature_catalogue c
WHERE c.is_active = TRUE AND c.category IN ('CLASS_A','CLASS_B')
ON CONFLICT (class_code, version, feature_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.fpo_bulk_import_jobs (
    import_job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    import_type text NOT NULL,
    source_format text NOT NULL,
    original_filename text NOT NULL,
    object_key text NOT NULL,
    file_checksum text NOT NULL,
    template_version integer NOT NULL DEFAULT 1,
    mode text NOT NULL DEFAULT 'DRY_RUN',
    status text NOT NULL DEFAULT 'UPLOADING',
    total_rows integer NOT NULL DEFAULT 0,
    valid_rows integer NOT NULL DEFAULT 0,
    invalid_rows integer NOT NULL DEFAULT 0,
    created_rows integer NOT NULL DEFAULT 0,
    updated_rows integer NOT NULL DEFAULT 0,
    skipped_rows integer NOT NULL DEFAULT 0,
    failed_rows integer NOT NULL DEFAULT 0,
    configuration_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    requested_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    started_at timestamptz,
    completed_at timestamptz,
    expires_at timestamptz NOT NULL DEFAULT (now() + interval '30 days'),
    error_code text,
    error_message text,
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_import_type CHECK (import_type IN ('FARMERS','FARMS','FARMERS_AND_FARMS')),
    CONSTRAINT ck_fpo_import_format CHECK (source_format IN ('CSV','XLSX')),
    CONSTRAINT ck_fpo_import_mode CHECK (mode IN ('DRY_RUN','COMMIT')),
    CONSTRAINT ck_fpo_import_status CHECK (status IN ('UPLOADING','QUEUED','PARSING','VALIDATING','DRY_RUN_READY','COMMITTING','COMPLETED','FAILED','CANCELLED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_bulk_import_jobs_owner ON public.fpo_bulk_import_jobs (fpo_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fpo_bulk_import_jobs_worker ON public.fpo_bulk_import_jobs (status, created_at);

CREATE TABLE IF NOT EXISTS public.fpo_bulk_import_rows (
    import_row_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    import_job_id uuid NOT NULL REFERENCES public.fpo_bulk_import_jobs(import_job_id) ON DELETE CASCADE,
    row_number integer NOT NULL,
    external_reference text,
    raw_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    normalized_payload jsonb,
    row_status text NOT NULL DEFAULT 'PENDING',
    error_items jsonb NOT NULL DEFAULT '[]'::jsonb,
    farmer_id uuid,
    farm_id uuid,
    idempotency_key text NOT NULL,
    processed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_import_row_status CHECK (row_status IN ('PENDING','VALID','INVALID','CREATED','UPDATED','SKIPPED','FAILED')),
    UNIQUE (import_job_id, row_number), UNIQUE (import_job_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_fpo_bulk_import_rows_status ON public.fpo_bulk_import_rows (import_job_id, row_status, row_number);

CREATE TABLE IF NOT EXISTS public.fpo_data_quality_issues (
    quality_issue_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    entity_type text NOT NULL,
    entity_id uuid,
    issue_code text NOT NULL,
    severity text NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    recommended_action text NOT NULL,
    deduplication_key text NOT NULL,
    status text NOT NULL DEFAULT 'OPEN',
    first_detected_at timestamptz NOT NULL DEFAULT now(),
    last_detected_at timestamptz NOT NULL DEFAULT now(),
    occurrence_count integer NOT NULL DEFAULT 1,
    resolved_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    resolved_at timestamptz,
    resolution_note text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT ck_fpo_quality_entity CHECK (entity_type IN ('ORGANIZATION','FARMER','FARM','CROP_CYCLE','OBSERVATION','PROJECTION')),
    CONSTRAINT ck_fpo_quality_severity CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    CONSTRAINT ck_fpo_quality_status CHECK (status IN ('OPEN','ACKNOWLEDGED','RESOLVED','IGNORED'))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_quality_active ON public.fpo_data_quality_issues (fpo_id, deduplication_key) WHERE status IN ('OPEN','ACKNOWLEDGED');
CREATE INDEX IF NOT EXISTS idx_fpo_quality_queue ON public.fpo_data_quality_issues (fpo_id, status, severity, last_detected_at DESC);

COMMIT;
