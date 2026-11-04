BEGIN;

ALTER TABLE public.fpo_quality_inspections
    ADD COLUMN IF NOT EXISTS inspection_code varchar(60),
    ADD COLUMN IF NOT EXISTS inspection_type varchar(30) NOT NULL DEFAULT 'RECEIVING',
    ADD COLUMN IF NOT EXISTS sample_reference varchar(80),
    ADD COLUMN IF NOT EXISTS sampled_quantity numeric(18,4),
    ADD COLUMN IF NOT EXISTS quantity_unit varchar(20),
    ADD COLUMN IF NOT EXISTS sampled_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS inspected_at timestamptz,
    ADD COLUMN IF NOT EXISTS inspector_name varchar(160),
    ADD COLUMN IF NOT EXISTS resulting_grade_code varchar(50),
    ADD COLUMN IF NOT EXISTS replacement_for_inspection_id uuid REFERENCES public.fpo_quality_inspections(inspection_id) ON DELETE SET NULL;

UPDATE public.fpo_quality_inspections SET inspection_code = COALESCE(inspection_code, 'INS-' || inspection_id::text) WHERE inspection_code IS NULL;
ALTER TABLE public.fpo_quality_inspections ALTER COLUMN inspection_code SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_quality_inspection_code ON public.fpo_quality_inspections (fpo_id,inspection_code);
ALTER TABLE public.fpo_quality_inspections DROP CONSTRAINT IF EXISTS ck_fpo_quality_inspection_status;
ALTER TABLE public.fpo_quality_inspections ADD CONSTRAINT ck_fpo_quality_inspection_status_hardened CHECK (status IN ('DRAFT','SAMPLED','IN_PROGRESS','COMPLETED','REVIEWED','VOIDED'));

CREATE TABLE IF NOT EXISTS public.fpo_quality_test_results (
    test_result_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    inspection_id uuid NOT NULL REFERENCES public.fpo_quality_inspections(inspection_id) ON DELETE RESTRICT, parameter_code varchar(60) NOT NULL,
    result_numeric numeric(18,6), result_text varchar(300), unit_code varchar(20), method_code varchar(60), lower_limit numeric(18,6), upper_limit numeric(18,6),
    pass_status varchar(20) NOT NULL DEFAULT 'PENDING', remarks text, created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_quality_test_pass CHECK (pass_status IN ('PENDING','PASS','FAIL','NOT_APPLICABLE')),
    UNIQUE (inspection_id,parameter_code)
);

COMMIT;
