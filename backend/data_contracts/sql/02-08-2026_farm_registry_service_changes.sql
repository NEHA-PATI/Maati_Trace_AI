BEGIN;

DROP INDEX IF EXISTS public.idx_farms_farmer;
DROP INDEX IF EXISTS public.idx_farms_fpo;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farms_h3_resolution_check'
    ) THEN
        ALTER TABLE public.farms
        ADD CONSTRAINT farms_h3_resolution_check
        CHECK (h3_resolution BETWEEN 7 AND 12)
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farms_h3_cell_count_check'
    ) THEN
        ALTER TABLE public.farms
        ADD CONSTRAINT farms_h3_cell_count_check
        CHECK (h3_cell_count > 0)
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farms_h3_array_count_check'
    ) THEN
        ALTER TABLE public.farms
        ADD CONSTRAINT farms_h3_array_count_check
        CHECK (cardinality(h3_cells) = h3_cell_count)
        NOT VALID;
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'farms_area_acres_check'
    ) THEN
        ALTER TABLE public.farms
        ADD CONSTRAINT farms_area_acres_check
        CHECK (area_acres IS NULL OR area_acres > 0)
        NOT VALID;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.farm_registry_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_farms_updated_at ON public.farms;

CREATE TRIGGER trg_farms_updated_at
BEFORE UPDATE
ON public.farms
FOR EACH ROW
EXECUTE FUNCTION public.farm_registry_set_updated_at();

COMMIT;