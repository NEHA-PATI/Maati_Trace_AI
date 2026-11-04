BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_inventory_reservations (
    reservation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    inventory_lot_id uuid NOT NULL REFERENCES public.fpo_inventory_lots(inventory_lot_id) ON DELETE RESTRICT, order_line_id uuid,
    quantity numeric(18,4) NOT NULL, quantity_unit varchar(20) NOT NULL, status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    idempotency_key varchar(120) NOT NULL, created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), released_at timestamptz,
    CONSTRAINT uq_fpo_reservation_key UNIQUE (fpo_id,idempotency_key), CONSTRAINT ck_fpo_reservation_status CHECK (status IN ('ACTIVE','RELEASED','CONSUMED')), CONSTRAINT ck_fpo_reservation_quantity CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS public.fpo_inventory_reconciliation_runs (
    reconciliation_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    status varchar(20) NOT NULL DEFAULT 'RUNNING', checked_lot_count integer NOT NULL DEFAULT 0, difference_count integer NOT NULL DEFAULT 0,
    details jsonb NOT NULL DEFAULT '{}'::jsonb, started_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz,
    CONSTRAINT ck_fpo_reconciliation_status CHECK (status IN ('RUNNING','PASSED','FAILED'))
);

CREATE TABLE IF NOT EXISTS public.fpo_commercial_contracts (
    contract_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    contract_code varchar(60) NOT NULL, counterparty_id uuid NOT NULL REFERENCES public.fpo_counterparties(counterparty_id) ON DELETE RESTRICT, opportunity_id uuid REFERENCES public.fpo_market_opportunities(opportunity_id) ON DELETE SET NULL,
    external_contract_reference varchar(120), title varchar(200) NOT NULL, contract_type varchar(30) NOT NULL, effective_date date NOT NULL, expiry_date date,
    currency_code char(3) NOT NULL DEFAULT 'INR', value_amount numeric(18,2), incoterm_code varchar(20), payment_terms_code varchar(40), quality_schema_id uuid REFERENCES public.fpo_quality_grading_schemas(quality_schema_id) ON DELETE SET NULL,
    delivery_terms text, source_document_artifact_id uuid, source_document_checksum varchar(128), status varchar(25) NOT NULL DEFAULT 'DRAFT', activated_at timestamptz,
    terminated_at timestamptz, termination_reason text, created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_contract_code UNIQUE (fpo_id,contract_code), CONSTRAINT ck_fpo_contract_status CHECK (status IN ('DRAFT','UNDER_REVIEW','ACTIVE','SUSPENDED','FULFILLED','EXPIRED','TERMINATED')), CONSTRAINT ck_fpo_contract_dates CHECK (expiry_date IS NULL OR expiry_date >= effective_date)
);

CREATE TABLE IF NOT EXISTS public.fpo_orders (
    order_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, order_code varchar(60) NOT NULL,
    counterparty_id uuid NOT NULL REFERENCES public.fpo_counterparties(counterparty_id) ON DELETE RESTRICT, contract_id uuid REFERENCES public.fpo_commercial_contracts(contract_id) ON DELETE SET NULL, opportunity_id uuid REFERENCES public.fpo_market_opportunities(opportunity_id) ON DELETE SET NULL,
    buyer_purchase_order_ref varchar(120), order_date date NOT NULL DEFAULT current_date, delivery_start_date date, delivery_end_date date, delivery_address_text varchar(400), currency_code char(3) NOT NULL DEFAULT 'INR',
    subtotal_amount numeric(18,2) NOT NULL DEFAULT 0, tax_amount numeric(18,2) NOT NULL DEFAULT 0, other_amount numeric(18,2) NOT NULL DEFAULT 0, total_amount numeric(18,2) NOT NULL DEFAULT 0,
    payment_status varchar(25) NOT NULL DEFAULT 'INFORMATIONAL', fulfillment_status varchar(25) NOT NULL DEFAULT 'UNFULFILLED', status varchar(25) NOT NULL DEFAULT 'DRAFT', confirmed_at timestamptz, cancelled_at timestamptz, cancellation_reason text,
    created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_order_code UNIQUE (fpo_id,order_code), CONSTRAINT ck_fpo_order_status CHECK (status IN ('DRAFT','CONFIRMED','ALLOCATING','READY_TO_DISPATCH','PARTIALLY_DISPATCHED','DISPATCHED','COMPLETED','CANCELLED')),
    CONSTRAINT ck_fpo_order_dates CHECK (delivery_end_date IS NULL OR delivery_start_date IS NULL OR delivery_end_date >= delivery_start_date)
);
CREATE TABLE IF NOT EXISTS public.fpo_order_lines (
    order_line_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, order_id uuid NOT NULL REFERENCES public.fpo_orders(order_id) ON DELETE CASCADE,
    line_number integer NOT NULL, commodity_code varchar(50) NOT NULL, variety_code varchar(50), grade_code varchar(50), ordered_quantity numeric(18,4) NOT NULL, allocated_quantity numeric(18,4) NOT NULL DEFAULT 0, dispatched_quantity numeric(18,4) NOT NULL DEFAULT 0, accepted_quantity numeric(18,4) NOT NULL DEFAULT 0, rejected_quantity numeric(18,4) NOT NULL DEFAULT 0,
    quantity_unit varchar(20) NOT NULL, unit_price numeric(18,4) NOT NULL DEFAULT 0, tax_rate numeric(9,4), line_total numeric(18,2) NOT NULL DEFAULT 0, quality_schema_id uuid REFERENCES public.fpo_quality_grading_schemas(quality_schema_id) ON DELETE SET NULL, status varchar(25) NOT NULL DEFAULT 'DRAFT',
    CONSTRAINT uq_fpo_order_line_number UNIQUE (order_id,line_number), CONSTRAINT ck_fpo_order_line_quantity CHECK (ordered_quantity > 0 AND allocated_quantity >= 0 AND dispatched_quantity >= 0 AND dispatched_quantity <= allocated_quantity)
);

CREATE TABLE IF NOT EXISTS public.fpo_dispatches (
    dispatch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, dispatch_code varchar(60) NOT NULL, order_id uuid NOT NULL REFERENCES public.fpo_orders(order_id) ON DELETE RESTRICT, warehouse_id uuid NOT NULL REFERENCES public.fpo_warehouses(warehouse_id) ON DELETE RESTRICT,
    logistics_counterparty_id uuid REFERENCES public.fpo_counterparties(counterparty_id) ON DELETE SET NULL, vehicle_reference_encrypted text, driver_name_encrypted text, driver_phone_encrypted text, transport_document_ref varchar(120), scheduled_departure_at timestamptz, departed_at timestamptz, estimated_arrival_at timestamptz, arrived_at timestamptz, delivery_confirmed_at timestamptz,
    proof_of_delivery_artifact_id uuid, status varchar(25) NOT NULL DEFAULT 'DRAFT', exception_reason_code varchar(60), created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_dispatch_code UNIQUE (fpo_id,dispatch_code), CONSTRAINT ck_fpo_dispatch_status CHECK (status IN ('DRAFT','PACKING','READY','IN_TRANSIT','DELIVERED','DELIVERY_EXCEPTION','CANCELLED'))
);
CREATE TABLE IF NOT EXISTS public.fpo_dispatch_items (
    dispatch_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, dispatch_id uuid NOT NULL REFERENCES public.fpo_dispatches(dispatch_id) ON DELETE CASCADE, order_line_id uuid NOT NULL REFERENCES public.fpo_order_lines(order_line_id) ON DELETE RESTRICT, inventory_lot_id uuid NOT NULL REFERENCES public.fpo_inventory_lots(inventory_lot_id) ON DELETE RESTRICT,
    quantity numeric(18,4) NOT NULL, quantity_unit varchar(20) NOT NULL, package_count integer, package_type_code varchar(40), traceability_code varchar(80) NOT NULL, status varchar(25) NOT NULL DEFAULT 'DRAFT', CONSTRAINT ck_fpo_dispatch_item_quantity CHECK (quantity > 0)
);

CREATE OR REPLACE FUNCTION public.prevent_fpo_inventory_ledger_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'FPO_INVENTORY_LEDGER_APPEND_ONLY'; END; $$;
DROP TRIGGER IF EXISTS trg_fpo_inventory_ledger_no_update ON public.fpo_inventory_ledger;
DROP TRIGGER IF EXISTS trg_fpo_inventory_ledger_no_delete ON public.fpo_inventory_ledger;
CREATE TRIGGER trg_fpo_inventory_ledger_no_update BEFORE UPDATE ON public.fpo_inventory_ledger FOR EACH ROW EXECUTE FUNCTION public.prevent_fpo_inventory_ledger_mutation();
CREATE TRIGGER trg_fpo_inventory_ledger_no_delete BEFORE DELETE ON public.fpo_inventory_ledger FOR EACH ROW EXECUTE FUNCTION public.prevent_fpo_inventory_ledger_mutation();

COMMIT;
