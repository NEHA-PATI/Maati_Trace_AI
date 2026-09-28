BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_alert_metric_registry (
    metric_key text PRIMARY KEY, display_name text NOT NULL, description text NOT NULL, unit text,
    value_type text NOT NULL, allowed_operators text[] NOT NULL DEFAULT '{}', minimum_threshold numeric,
    maximum_threshold numeric, supported_scopes text[] NOT NULL DEFAULT '{}', data_source text NOT NULL,
    freshness_requirement interval, risk_level text NOT NULL DEFAULT 'MEDIUM', status text NOT NULL DEFAULT 'ACTIVE',
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO public.fpo_alert_metric_registry (metric_key,display_name,description,unit,value_type,allowed_operators,supported_scopes,data_source,risk_level)
VALUES
 ('OBSERVATION_AGE_DAYS','Observation age','Days since the latest trusted observation.','days','NUMBER',ARRAY['GREATER_THAN','LESS_THAN'],ARRAY['PORTFOLIO','SEGMENT','CROP','GEOGRAPHY'],'analytics','MEDIUM'),
 ('OPEN_ALERT_COUNT','Open alerts','Number of unresolved operational alerts.','alerts','NUMBER',ARRAY['GREATER_THAN','EQUALS'],ARRAY['PORTFOLIO','SEGMENT','GEOGRAPHY'],'fpo_management','MEDIUM'),
 ('FARM_CONDITION_STATUS','Farm condition','Latest server-calculated farm condition status.','status','ENUM',ARRAY['EQUALS'],ARRAY['PORTFOLIO','SEGMENT','CROP','GEOGRAPHY'],'analytics','HIGH'),
 ('PORTFOLIO_AREA_ACRES','Portfolio area','Active relationship farm area.','acres','NUMBER',ARRAY['GREATER_THAN','LESS_THAN'],ARRAY['PORTFOLIO','GEOGRAPHY'],'farm_registry','LOW')
ON CONFLICT (metric_key) DO UPDATE SET display_name=EXCLUDED.display_name,description=EXCLUDED.description,allowed_operators=EXCLUDED.allowed_operators,supported_scopes=EXCLUDED.supported_scopes,updated_at=now();

CREATE TABLE IF NOT EXISTS public.fpo_alert_rules (
    alert_rule_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    name varchar(200) NOT NULL, rule_type text NOT NULL DEFAULT 'THRESHOLD', feature_metric text NOT NULL REFERENCES public.fpo_alert_metric_registry(metric_key) ON DELETE RESTRICT,
    scope_type text NOT NULL DEFAULT 'PORTFOLIO', scope_configuration jsonb NOT NULL DEFAULT '{}'::jsonb, condition_configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    severity text NOT NULL DEFAULT 'WARNING', deduplication_window_minutes integer NOT NULL DEFAULT 360, cooldown_minutes integer NOT NULL DEFAULT 720,
    active_from timestamptz, active_until timestamptz, status text NOT NULL DEFAULT 'DRAFT', rule_version integer NOT NULL DEFAULT 1,
    created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, published_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    published_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_rule_scope CHECK (scope_type IN ('PORTFOLIO','SEGMENT','CROP','GEOGRAPHY')),
    CONSTRAINT ck_fpo_rule_severity CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    CONSTRAINT ck_fpo_rule_status CHECK (status IN ('DRAFT','ACTIVE','PAUSED','ARCHIVED')),
    CONSTRAINT ck_fpo_rule_windows CHECK (deduplication_window_minutes > 0 AND cooldown_minutes > 0)
);
CREATE INDEX IF NOT EXISTS idx_fpo_alert_rules_owner ON public.fpo_alert_rules (fpo_id,status,updated_at DESC);

ALTER TABLE public.fpo_operational_alerts DROP CONSTRAINT IF EXISTS ck_fpo_alert_status;
ALTER TABLE public.fpo_operational_alerts DROP CONSTRAINT IF EXISTS ck_fpo_alert_status_b5;
ALTER TABLE public.fpo_operational_alerts ADD CONSTRAINT ck_fpo_alert_status_b5 CHECK (status IN ('OPEN','ACKNOWLEDGED','IN_PROGRESS','RESOLVED','DISMISSED'));
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS rule_id uuid REFERENCES public.fpo_alert_rules(alert_rule_id) ON DELETE SET NULL;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS rule_version integer;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS farmer_id uuid;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS farm_id uuid;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS crop_cycle_id uuid;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS assigned_task_id uuid;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS acknowledgement_note text;
ALTER TABLE public.fpo_operational_alerts ADD COLUMN IF NOT EXISTS resolution_code text;

CREATE TABLE IF NOT EXISTS public.fpo_advisory_templates (
    template_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    template_code varchar(100) NOT NULL, name varchar(200) NOT NULL, advisory_type text NOT NULL, crop_code text, stage_code text,
    language_code varchar(10) NOT NULL, title_template text NOT NULL, body_template text NOT NULL, voice_object_key text,
    required_consent_scopes text[] NOT NULL DEFAULT ARRAY['ADVISORY_MESSAGE'], status text NOT NULL DEFAULT 'DRAFT', version integer NOT NULL DEFAULT 1,
    safety_review_status text NOT NULL DEFAULT 'PENDING', safety_reviewed_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL, safety_reviewed_at timestamptz,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_advisory_type CHECK (advisory_type IN ('GENERAL','NUTRIENT','CROP_PROTECTION','WEATHER','IRRIGATION','STAGE_ACTIVITY')),
    CONSTRAINT ck_fpo_template_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED')),
    CONSTRAINT ck_fpo_safety_status CHECK (safety_review_status IN ('NOT_REQUIRED','PENDING','APPROVED','REJECTED')),
    UNIQUE (fpo_id,template_code,version,language_code)
);
CREATE TABLE IF NOT EXISTS public.fpo_advisory_campaigns (
    campaign_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    name varchar(200) NOT NULL, template_id uuid NOT NULL REFERENCES public.fpo_advisory_templates(template_id) ON DELETE RESTRICT, segment_id uuid REFERENCES public.fpo_farmer_segments(segment_id) ON DELETE SET NULL,
    recipient_filter_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb, channel text NOT NULL DEFAULT 'IN_APP', language_strategy text NOT NULL DEFAULT 'FARMER_PREFERENCE', fixed_language_code text,
    status text NOT NULL DEFAULT 'DRAFT', scheduled_at timestamptz, recipient_count integer NOT NULL DEFAULT 0, eligible_count integer NOT NULL DEFAULT 0, suppressed_count integer NOT NULL DEFAULT 0,
    sent_count integer NOT NULL DEFAULT 0, delivered_count integer NOT NULL DEFAULT 0, failed_count integer NOT NULL DEFAULT 0, created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    approved_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL, approved_at timestamptz, started_at timestamptz, completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_campaign_channel CHECK (channel IN ('IN_APP','SMS','WHATSAPP','VOICE')),
    CONSTRAINT ck_fpo_campaign_language CHECK (language_strategy IN ('FARMER_PREFERENCE','FIXED')),
    CONSTRAINT ck_fpo_campaign_status CHECK (status IN ('DRAFT','SCHEDULED','SENDING','COMPLETED','CANCELLED','FAILED'))
);
CREATE TABLE IF NOT EXISTS public.fpo_advisory_recipients (
    campaign_recipient_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), campaign_id uuid NOT NULL REFERENCES public.fpo_advisory_campaigns(campaign_id) ON DELETE CASCADE,
    farmer_id uuid NOT NULL, relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE RESTRICT, consent_id uuid NOT NULL REFERENCES public.fpo_farmer_relationship_consents(consent_id) ON DELETE RESTRICT,
    language_code text NOT NULL, destination_ciphertext bytea, rendered_title text NOT NULL, rendered_body text NOT NULL,
    status text NOT NULL DEFAULT 'ELIGIBLE', suppression_reason text, provider_message_id text, attempts integer NOT NULL DEFAULT 0,
    last_error_code text, queued_at timestamptz, sent_at timestamptz, delivered_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_recipient_status CHECK (status IN ('ELIGIBLE','SUPPRESSED','QUEUED','SENT','DELIVERED','FAILED','CANCELLED')), UNIQUE (campaign_id,farmer_id)
);
CREATE INDEX IF NOT EXISTS idx_fpo_campaign_recipients_queue ON public.fpo_advisory_recipients (campaign_id,status,updated_at);

CREATE TABLE IF NOT EXISTS public.agronomy_recommendation_catalogue (
    recommendation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), recommendation_type text NOT NULL, crop_code text NOT NULL, variety_code text, stage_code text, condition_code text,
    product_or_nutrient_code text, display_name text NOT NULL, instruction_text text NOT NULL, quantity_value numeric, quantity_unit text, application_method text,
    safety_interval_days integer, pre_harvest_interval_days integer, source_reference text NOT NULL, jurisdiction_code text NOT NULL, valid_from date NOT NULL, valid_until date,
    status text NOT NULL DEFAULT 'DRAFT', approved_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL, approved_at timestamptz, version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), CONSTRAINT ck_agronomy_status CHECK (status IN ('DRAFT','APPROVED','RETIRED'))
);

COMMIT;
