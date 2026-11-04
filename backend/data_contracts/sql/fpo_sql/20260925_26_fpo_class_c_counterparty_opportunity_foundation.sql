BEGIN;

-- Class C v4 is additive and intentionally remains DRAFT until the C0-C9 gates pass.
INSERT INTO public.fpo_feature_catalogue
    (feature_key, display_name, description, category, dependencies, risk_level, navigation_key, sort_order)
VALUES
 ('PROCUREMENT_PLANNING','Procurement planning','Plan commercial procurement by season, crop, geography and segment.','CLASS_C',ARRAY['SEASON_PLANNING','YIELD_FORECASTS_STANDARD'],'HIGH','procurement',400),
 ('PRODUCE_AGGREGATION_LOTS','Produce aggregation lots','Receive approved farmer contributions into traceable lots.','CLASS_C',ARRAY['PROCUREMENT_PLANNING'],'HIGH','lots',410),
 ('QUALITY_GRADING','Quality and grading','Inspect and grade aggregated produce with governed schemas.','CLASS_C',ARRAY['PRODUCE_AGGREGATION_LOTS'],'HIGH','quality',420),
 ('END_TO_END_TRACEABILITY','End-to-end traceability','Maintain internal lot lineage and minimized traceability views.','CLASS_C',ARRAY['PRODUCE_AGGREGATION_LOTS','QUALITY_GRADING'],'HIGH','traceability',430),
 ('WAREHOUSE_INVENTORY','Warehouse and inventory','Operate warehouses and append-only inventory ledgers.','CLASS_C',ARRAY['PRODUCE_AGGREGATION_LOTS'],'HIGH','inventory',440),
 ('BUYER_EXPORTER_CRM','Buyers and exporters','Manage governed counterparty records and due diligence.','CLASS_C',ARRAY['FPO_PROFILE_MANAGEMENT'],'HIGH','counterparties',450),
 ('MARKET_OPPORTUNITIES','Market opportunities','Manage qualified commercial opportunity pipelines.','CLASS_C',ARRAY['BUYER_EXPORTER_CRM'],'MEDIUM','opportunities',460),
 ('CONTRACT_AND_ORDER_MANAGEMENT','Contracts and orders','Track commercial contracts, orders and fulfillment.','CLASS_C',ARRAY['MARKET_OPPORTUNITIES'],'HIGH','orders',470),
 ('LOGISTICS_COORDINATION','Logistics and dispatch','Coordinate compatible-stock allocations and dispatches.','CLASS_C',ARRAY['WAREHOUSE_INVENTORY','CONTRACT_AND_ORDER_MANAGEMENT'],'HIGH','logistics',480),
 ('PRICE_INTELLIGENCE','Price intelligence','View source-aware price observations with freshness.','CLASS_C',ARRAY['CROP_PORTFOLIO_ADVANCED'],'MEDIUM','prices',490),
 ('YIELD_FORECASTING_ADVANCED','Advanced production forecasting','Use provenance-aware advanced yield and surplus forecasts.','CLASS_C',ARRAY['YIELD_FORECASTS_STANDARD'],'MEDIUM','forecasts',500),
 ('COMPLIANCE_AND_CERTIFICATIONS','Compliance and certifications','Track compliance requirements, certificates and expiry.','CLASS_C',ARRAY['FPO_PROFILE_MANAGEMENT'],'HIGH','compliance',510),
 ('EXPORT_DOCUMENT_PACKS','Export document packs','Generate governed export-ready document packs.','CLASS_C',ARRAY['COMPLIANCE_AND_CERTIFICATIONS','CONTRACT_AND_ORDER_MANAGEMENT'],'HIGH','exports',520),
 ('FINANCE_INSURANCE_DATA_PACKS','Finance and insurance data packs','Generate consent-bound minimized finance or insurance data packs.','CLASS_C',ARRAY['ADVANCED_REPORTS'],'CRITICAL','data-packs',530),
 ('SUSTAINABILITY_ANALYTICS','Sustainability and impact','Calculate coverage-aware sustainability indicators.','CLASS_C',ARRAY['PORTFOLIO_TRENDS'],'MEDIUM','sustainability',540),
 ('CUSTOM_DASHBOARDS','Custom dashboards','Configure governed commercial dashboards.','CLASS_C',ARRAY['ADVANCED_REPORTS'],'MEDIUM','dashboards',550),
 ('SCHEDULED_REPORTS','Scheduled reports','Schedule governed commercial reports.','CLASS_C',ARRAY['ADVANCED_REPORTS','DATA_EXPORT'],'HIGH','reports',560),
 ('ENTERPRISE_API_ACCESS','Enterprise API access','Expose approved scoped integrations through the gateway.','CLASS_C',ARRAY['END_TO_END_TRACEABILITY'],'CRITICAL','integrations',570),
 ('OUTBOUND_WEBHOOKS','Outbound webhooks','Deliver approved domain events to governed destinations.','CLASS_C',ARRAY['ENTERPRISE_API_ACCESS'],'CRITICAL','integrations',580)
ON CONFLICT (feature_key) DO UPDATE SET
 display_name=EXCLUDED.display_name, description=EXCLUDED.description, category='CLASS_C',
 dependencies=EXCLUDED.dependencies, risk_level=EXCLUDED.risk_level,
 navigation_key=EXCLUDED.navigation_key, sort_order=EXCLUDED.sort_order, updated_at=now();

INSERT INTO public.fpo_plan_versions
    (class_code, version, status, name, description, publication_reason)
VALUES ('C',4,'DRAFT','Commercial Enterprise v4','Class A and B inheritance plus governed commercial and enterprise operations.','Class C implementation foundation; pending C0-C9 release gates')
ON CONFLICT (class_code, version) DO NOTHING;

INSERT INTO public.fpo_class_feature_versions
    (class_code, version, feature_key, enabled, configuration, published_at)
SELECT 'C', 4, c.feature_key, TRUE,
       CASE c.feature_key
         WHEN 'ENTERPRISE_API_ACCESS' THEN '{"enabled":false,"emergency_disable":true,"default_rate_limit_per_minute":60}'::jsonb
         WHEN 'OUTBOUND_WEBHOOKS' THEN '{"enabled":false,"emergency_disable":true}'::jsonb
         WHEN 'FINANCE_INSURANCE_DATA_PACKS' THEN '{"enabled":false,"require_destination_grant":true}'::jsonb
         ELSE '{}'::jsonb
       END,
       NULL
FROM public.fpo_feature_catalogue c
WHERE c.is_active = TRUE AND c.category IN ('CLASS_A','CLASS_B','CLASS_C')
ON CONFLICT (class_code, version, feature_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.fpo_counterparties (
    counterparty_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    counterparty_code varchar(40) NOT NULL,
    counterparty_type varchar(30) NOT NULL,
    legal_name varchar(200) NOT NULL,
    trade_name varchar(200),
    registration_number varchar(80),
    tax_identifier_encrypted text,
    country_code char(2) NOT NULL DEFAULT 'IN',
    state_code varchar(20), district_code varchar(20),
    address_line_1 varchar(200), address_line_2 varchar(200), postal_code varchar(20),
    website_url varchar(500), preferred_currency char(3) NOT NULL DEFAULT 'INR',
    payment_terms_code varchar(40), risk_rating varchar(20),
    due_diligence_status varchar(30) NOT NULL DEFAULT 'PENDING',
    due_diligence_reviewed_at timestamptz, due_diligence_expires_at timestamptz,
    notes_encrypted text, status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_counterparty_code UNIQUE (fpo_id,counterparty_code),
    CONSTRAINT ck_fpo_counterparty_type CHECK (counterparty_type IN ('BUYER','EXPORTER','PROCESSOR','RETAILER','INSTITUTIONAL_BUYER','LOGISTICS_PROVIDER','LABORATORY','WAREHOUSE_OPERATOR','LENDER','INSURER','OTHER')),
    CONSTRAINT ck_fpo_counterparty_due_diligence CHECK (due_diligence_status IN ('PENDING','UNDER_REVIEW','APPROVED','REJECTED','EXPIRED')),
    CONSTRAINT ck_fpo_counterparty_status CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_counterparties_owner ON public.fpo_counterparties (fpo_id,counterparty_type,status,updated_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_counterparty_contacts (
    contact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    counterparty_id uuid NOT NULL REFERENCES public.fpo_counterparties(counterparty_id) ON DELETE CASCADE,
    full_name varchar(160) NOT NULL, designation varchar(120), email_encrypted text, phone_encrypted text,
    preferred_channel varchar(20), is_primary boolean NOT NULL DEFAULT false,
    data_processing_notice_sent_at timestamptz, status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_counterparty_contact_status CHECK (status IN ('ACTIVE','INACTIVE'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_counterparty_contacts_owner ON public.fpo_counterparty_contacts (fpo_id,counterparty_id,status);

CREATE TABLE IF NOT EXISTS public.fpo_market_opportunities (
    opportunity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    opportunity_code varchar(40) NOT NULL, counterparty_id uuid NOT NULL REFERENCES public.fpo_counterparties(counterparty_id) ON DELETE RESTRICT,
    title varchar(200) NOT NULL, commodity_code varchar(50) NOT NULL, variety_code varchar(50), quality_grade_code varchar(50),
    target_quantity numeric(18,4) NOT NULL, quantity_unit varchar(20) NOT NULL, target_price numeric(18,2), currency_code char(3) NOT NULL DEFAULT 'INR',
    delivery_start_date date, delivery_end_date date, delivery_location_text varchar(300), source_channel varchar(30) NOT NULL DEFAULT 'DIRECT',
    probability_percent numeric(5,2), owner_notes_encrypted text,
    stage varchar(30) NOT NULL DEFAULT 'DRAFT', lost_reason_code varchar(50), closed_at timestamptz,
    created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_opportunity_code UNIQUE (fpo_id,opportunity_code),
    CONSTRAINT ck_fpo_opportunity_stage CHECK (stage IN ('DRAFT','QUALIFYING','PROPOSAL','NEGOTIATION','WON','LOST','CANCELLED')),
    CONSTRAINT ck_fpo_opportunity_quantity CHECK (target_quantity > 0),
    CONSTRAINT ck_fpo_opportunity_probability CHECK (probability_percent IS NULL OR (probability_percent >= 0 AND probability_percent <= 100)),
    CONSTRAINT ck_fpo_opportunity_dates CHECK (delivery_end_date IS NULL OR delivery_start_date IS NULL OR delivery_end_date >= delivery_start_date)
);
CREATE INDEX IF NOT EXISTS idx_fpo_opportunities_pipeline ON public.fpo_market_opportunities (fpo_id,stage,updated_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_commercial_audit_events (
    audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    actor_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, action text NOT NULL, resource_type text NOT NULL,
    resource_id uuid, reason text, correlation_id text, metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_fpo_commercial_audit ON public.fpo_commercial_audit_events (fpo_id,created_at DESC);

COMMIT;
