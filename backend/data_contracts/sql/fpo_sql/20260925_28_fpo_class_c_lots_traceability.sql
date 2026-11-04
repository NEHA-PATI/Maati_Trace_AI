BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.fpo_aggregation_lots (
    lot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    lot_code varchar(60) NOT NULL, procurement_plan_id uuid REFERENCES public.fpo_procurement_plans(procurement_plan_id) ON DELETE SET NULL,
    warehouse_id uuid, storage_location_id uuid, commodity_code varchar(50) NOT NULL, variety_code varchar(50), crop_year smallint NOT NULL,
    season_code varchar(40), declared_grade_code varchar(50), received_quantity numeric(18,4) NOT NULL DEFAULT 0,
    accepted_quantity numeric(18,4) NOT NULL DEFAULT 0, rejected_quantity numeric(18,4) NOT NULL DEFAULT 0, available_quantity numeric(18,4) NOT NULL DEFAULT 0,
    quantity_unit varchar(20) NOT NULL, harvest_start_date date, harvest_end_date date, aggregation_started_at timestamptz NOT NULL DEFAULT now(),
    sealed_at timestamptz, closed_at timestamptz, traceability_code varchar(80) NOT NULL, traceability_hash varchar(128),
    status varchar(25) NOT NULL DEFAULT 'OPEN', created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_lot_code UNIQUE (fpo_id,lot_code),
    CONSTRAINT ck_fpo_lot_status CHECK (status IN ('OPEN','RECEIVING','SEALED','QUALITY_HOLD','AVAILABLE','ALLOCATED','DISPATCHED','CLOSED','RECALLED')),
    CONSTRAINT ck_fpo_lot_quantities CHECK (received_quantity >= 0 AND accepted_quantity >= 0 AND rejected_quantity >= 0 AND available_quantity >= 0 AND accepted_quantity + rejected_quantity <= received_quantity),
    CONSTRAINT ck_fpo_lot_dates CHECK (harvest_end_date IS NULL OR harvest_start_date IS NULL OR harvest_end_date >= harvest_start_date)
);
CREATE INDEX IF NOT EXISTS idx_fpo_lots_operational ON public.fpo_aggregation_lots (fpo_id,status,commodity_code,updated_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_lot_sources (
    lot_source_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    lot_id uuid NOT NULL REFERENCES public.fpo_aggregation_lots(lot_id) ON DELETE RESTRICT, source_sequence integer NOT NULL,
    farmer_id uuid NOT NULL REFERENCES public.farmer_profiles(farmer_id) ON DELETE RESTRICT, farm_id uuid NOT NULL, crop_cycle_id uuid,
    relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE RESTRICT,
    consent_id uuid NOT NULL REFERENCES public.fpo_farmer_relationship_consents(consent_id) ON DELETE RESTRICT,
    source_receipt_code varchar(60) NOT NULL, delivered_at timestamptz NOT NULL DEFAULT now(), gross_quantity numeric(18,4) NOT NULL,
    deduction_quantity numeric(18,4) NOT NULL DEFAULT 0, accepted_quantity numeric(18,4) NOT NULL, rejected_quantity numeric(18,4) NOT NULL DEFAULT 0,
    quantity_unit varchar(20) NOT NULL, declared_harvest_date date, collection_point_code varchar(60), source_grade_code varchar(50),
    source_price numeric(18,2), currency_code char(3), payment_reference_external varchar(120), source_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(25) NOT NULL DEFAULT 'ACCEPTED', created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_source_receipt UNIQUE (fpo_id,source_receipt_code), CONSTRAINT uq_fpo_lot_source_sequence UNIQUE (lot_id,source_sequence),
    CONSTRAINT ck_fpo_source_status CHECK (status IN ('PENDING','ACCEPTED','REJECTED','REVERSED')),
    CONSTRAINT ck_fpo_source_quantities CHECK (gross_quantity > 0 AND deduction_quantity >= 0 AND accepted_quantity >= 0 AND rejected_quantity >= 0 AND accepted_quantity + rejected_quantity + deduction_quantity <= gross_quantity)
);
CREATE INDEX IF NOT EXISTS idx_fpo_lot_sources_lineage ON public.fpo_lot_sources (fpo_id,lot_id,farmer_id);

CREATE TABLE IF NOT EXISTS public.fpo_lot_events (
    lot_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    lot_id uuid NOT NULL REFERENCES public.fpo_aggregation_lots(lot_id) ON DELETE RESTRICT, event_sequence bigint NOT NULL,
    event_type varchar(40) NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), actor_type varchar(30) NOT NULL, actor_id varchar(100) NOT NULL,
    location_code varchar(60), quantity_delta numeric(18,4), unit_code varchar(20), metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    previous_event_hash varchar(128), event_hash varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_lot_event_sequence UNIQUE (lot_id,event_sequence), CONSTRAINT uq_fpo_lot_event_hash UNIQUE (lot_id,event_hash)
);
CREATE INDEX IF NOT EXISTS idx_fpo_lot_events_order ON public.fpo_lot_events (lot_id,event_sequence);

CREATE TABLE IF NOT EXISTS public.fpo_traceability_views (
    traceability_view_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    lot_id uuid NOT NULL REFERENCES public.fpo_aggregation_lots(lot_id) ON DELETE CASCADE, schema_key varchar(100) NOT NULL, schema_version integer NOT NULL DEFAULT 1,
    minimized_payload jsonb NOT NULL DEFAULT '{}'::jsonb, generated_at timestamptz NOT NULL DEFAULT now(), source_watermark timestamptz,
    UNIQUE (lot_id,schema_key,schema_version)
);

COMMIT;
