BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_quality_grading_schemas (
    quality_schema_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), schema_key varchar(100) NOT NULL, version integer NOT NULL DEFAULT 1,
    name varchar(180) NOT NULL, commodity_code varchar(50) NOT NULL, grade_definitions jsonb NOT NULL DEFAULT '[]'::jsonb,
    parameter_definitions jsonb NOT NULL DEFAULT '[]'::jsonb, status varchar(20) NOT NULL DEFAULT 'DRAFT', jurisdiction_code varchar(30),
    created_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, published_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    published_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_quality_schema UNIQUE (schema_key,version), CONSTRAINT ck_fpo_quality_schema_status CHECK (status IN ('DRAFT','PUBLISHED','RETIRED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_quality_inspections (
    inspection_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    lot_id uuid NOT NULL REFERENCES public.fpo_aggregation_lots(lot_id) ON DELETE RESTRICT, quality_schema_id uuid NOT NULL REFERENCES public.fpo_quality_grading_schemas(quality_schema_id) ON DELETE RESTRICT,
    status varchar(25) NOT NULL DEFAULT 'DRAFT', measured_values jsonb NOT NULL DEFAULT '{}'::jsonb, calculated_grade_code varchar(50),
    disposition varchar(25) NOT NULL DEFAULT 'PENDING', inspected_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    reviewed_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL, reviewed_at timestamptz, reviewer_note text,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_quality_inspection_status CHECK (status IN ('DRAFT','SUBMITTED','UNDER_REVIEW','REVIEWED','CANCELLED')),
    CONSTRAINT ck_fpo_quality_disposition CHECK (disposition IN ('PENDING','PASS','HOLD','REJECT'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_quality_inspections_queue ON public.fpo_quality_inspections (fpo_id,status,created_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_warehouses (
    warehouse_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    warehouse_code varchar(50) NOT NULL, name varchar(180) NOT NULL, address_text varchar(500), capacity_quantity numeric(18,4), quantity_unit varchar(20),
    status varchar(20) NOT NULL DEFAULT 'ACTIVE', created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), CONSTRAINT uq_fpo_warehouse_code UNIQUE (fpo_id,warehouse_code),
    CONSTRAINT ck_fpo_warehouse_status CHECK (status IN ('ACTIVE','INACTIVE'))
);

CREATE TABLE IF NOT EXISTS public.fpo_inventory_lots (
    inventory_lot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    lot_id uuid NOT NULL REFERENCES public.fpo_aggregation_lots(lot_id) ON DELETE RESTRICT, warehouse_id uuid NOT NULL REFERENCES public.fpo_warehouses(warehouse_id) ON DELETE RESTRICT,
    location_code varchar(60), grade_code varchar(50), received_quantity numeric(18,4) NOT NULL, on_hand_quantity numeric(18,4) NOT NULL,
    reserved_quantity numeric(18,4) NOT NULL DEFAULT 0, quarantine_quantity numeric(18,4) NOT NULL DEFAULT 0, quantity_unit varchar(20) NOT NULL,
    status varchar(25) NOT NULL DEFAULT 'AVAILABLE', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_inventory_lot UNIQUE (fpo_id,lot_id,warehouse_id,location_code), CONSTRAINT ck_fpo_inventory_status CHECK (status IN ('AVAILABLE','QUARANTINE','DEPLETED','CLOSED')),
    CONSTRAINT ck_fpo_inventory_quantities CHECK (received_quantity >= 0 AND on_hand_quantity >= 0 AND reserved_quantity >= 0 AND quarantine_quantity >= 0 AND reserved_quantity + quarantine_quantity <= on_hand_quantity)
);
CREATE INDEX IF NOT EXISTS idx_fpo_inventory_owner ON public.fpo_inventory_lots (fpo_id,warehouse_id,status,updated_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_inventory_ledger (
    ledger_entry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    inventory_lot_id uuid NOT NULL REFERENCES public.fpo_inventory_lots(inventory_lot_id) ON DELETE RESTRICT, entry_sequence bigint NOT NULL,
    entry_type varchar(30) NOT NULL, quantity_delta numeric(18,4) NOT NULL, quantity_unit varchar(20) NOT NULL, reference_code varchar(80) NOT NULL,
    reason text, evidence_object_key text, actor_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_inventory_ledger_sequence UNIQUE (inventory_lot_id,entry_sequence), CONSTRAINT uq_fpo_inventory_reference UNIQUE (fpo_id,reference_code),
    CONSTRAINT ck_fpo_inventory_entry_type CHECK (entry_type IN ('RECEIPT','RESERVATION','RELEASE','TRANSFER_IN','TRANSFER_OUT','DISPATCH','ADJUSTMENT','LOSS','REVERSAL')),
    CONSTRAINT ck_fpo_inventory_quantity CHECK (quantity_delta <> 0)
);
CREATE INDEX IF NOT EXISTS idx_fpo_inventory_ledger_history ON public.fpo_inventory_ledger (fpo_id,inventory_lot_id,created_at DESC);

COMMIT;
