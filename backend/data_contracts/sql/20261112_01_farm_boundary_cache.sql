BEGIN;

ALTER TABLE public.farms
    ADD COLUMN IF NOT EXISTS boundary_hash text;

CREATE INDEX IF NOT EXISTS idx_farms_boundary_hash
    ON public.farms (farm_id, boundary_hash);

COMMIT;
