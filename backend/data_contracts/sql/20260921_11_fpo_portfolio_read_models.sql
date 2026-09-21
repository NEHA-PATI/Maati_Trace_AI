BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_portfolio_summary (
    fpo_id uuid PRIMARY KEY REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    active_farmer_count integer NOT NULL DEFAULT 0,
    pending_farmer_count integer NOT NULL DEFAULT 0,
    active_farm_count integer NOT NULL DEFAULT 0,
    registered_area_acres numeric(16,4) NOT NULL DEFAULT 0,
    active_crop_count integer NOT NULL DEFAULT 0,
    district_count integer NOT NULL DEFAULT 0,
    block_count integer NOT NULL DEFAULT 0,
    village_count integer NOT NULL DEFAULT 0,
    open_alert_count integer NOT NULL DEFAULT 0,
    attention_farm_count integer NOT NULL DEFAULT 0,
    critical_farm_count integer NOT NULL DEFAULT 0,
    data_through timestamptz,
    calculation_version text NOT NULL DEFAULT 'fpo-portfolio-v1',
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.fpo_farmer_portfolio (
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    farmer_id uuid NOT NULL REFERENCES public.farmer_profiles(farmer_id) ON DELETE CASCADE,
    farmer_name text NOT NULL,
    phone_masked text,
    district_code integer,
    district_name text,
    block_code integer,
    block_name text,
    village_name text,
    farm_count integer NOT NULL DEFAULT 0,
    area_acres numeric(14,4) NOT NULL DEFAULT 0,
    active_crop_codes text[] NOT NULL DEFAULT '{}',
    condition_status text NOT NULL DEFAULT 'UNKNOWN',
    highest_alert_severity text,
    open_alert_count integer NOT NULL DEFAULT 0,
    latest_observation_at timestamptz,
    latest_analysis_date date,
    relationship_status text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (fpo_id, farmer_id)
);

CREATE INDEX IF NOT EXISTS idx_fpo_farmer_portfolio_name
    ON public.fpo_farmer_portfolio (fpo_id, farmer_name, farmer_id);
CREATE INDEX IF NOT EXISTS idx_fpo_farmer_portfolio_filters
    ON public.fpo_farmer_portfolio (fpo_id, district_code, block_code, relationship_status);

COMMIT;
