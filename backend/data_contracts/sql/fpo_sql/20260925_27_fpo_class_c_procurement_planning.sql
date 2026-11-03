BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_procurement_plans (
    procurement_plan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    plan_code varchar(40) NOT NULL, revision_no integer NOT NULL DEFAULT 1, supersedes_plan_id uuid REFERENCES public.fpo_procurement_plans(procurement_plan_id) ON DELETE SET NULL,
    name varchar(180) NOT NULL, season_code varchar(40) NOT NULL, season_year smallint NOT NULL, start_date date NOT NULL, end_date date NOT NULL,
    currency_code char(3) NOT NULL DEFAULT 'INR', status varchar(25) NOT NULL DEFAULT 'DRAFT', approved_at timestamptz, approved_by_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    locked_at timestamptz, notes text, created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT uq_fpo_procurement_plan_code UNIQUE (fpo_id,plan_code,revision_no),
    CONSTRAINT ck_fpo_procurement_plan_status CHECK (status IN ('DRAFT','UNDER_REVIEW','APPROVED','ACTIVE','COMPLETED','CANCELLED')),
    CONSTRAINT ck_fpo_procurement_plan_dates CHECK (end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS idx_fpo_procurement_plans_owner ON public.fpo_procurement_plans (fpo_id,status,updated_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_procurement_plan_items (
    procurement_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    procurement_plan_id uuid NOT NULL REFERENCES public.fpo_procurement_plans(procurement_plan_id) ON DELETE CASCADE,
    commodity_code varchar(50) NOT NULL, variety_code varchar(50), quality_grade_code varchar(50), district_code varchar(20), block_code varchar(20), segment_id uuid,
    target_quantity numeric(18,4) NOT NULL, quantity_unit varchar(20) NOT NULL, forecast_available_quantity numeric(18,4), committed_quantity numeric(18,4) NOT NULL DEFAULT 0, procured_quantity numeric(18,4) NOT NULL DEFAULT 0,
    target_min_price numeric(18,2), target_max_price numeric(18,2), forecast_snapshot_id uuid, shortfall_threshold_percent numeric(5,2), status varchar(25) NOT NULL DEFAULT 'DRAFT',
    created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version_no integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_procurement_item_status CHECK (status IN ('DRAFT','ACTIVE','COMPLETED','CANCELLED')),
    CONSTRAINT ck_fpo_procurement_item_quantity CHECK (target_quantity > 0 AND committed_quantity >= 0 AND procured_quantity >= 0),
    CONSTRAINT ck_fpo_procurement_item_prices CHECK (target_max_price IS NULL OR target_min_price IS NULL OR target_max_price >= target_min_price)
);
CREATE INDEX IF NOT EXISTS idx_fpo_procurement_items_plan ON public.fpo_procurement_plan_items (fpo_id,procurement_plan_id,commodity_code);

COMMIT;
