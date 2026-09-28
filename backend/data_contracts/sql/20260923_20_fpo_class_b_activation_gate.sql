BEGIN;

-- B1/B2 are implemented, but the specification reserves activation for B8.
-- Keep the plan draft until all Class B workstreams and release gates pass.
UPDATE public.fpo_plan_versions
SET status = 'DRAFT', published_at = NULL, published_by = NULL,
    effective_from = NULL,
    publication_reason = 'Class B foundation and bulk onboarding implemented; awaiting remaining Class B release gates.'
WHERE class_code = 'B' AND version = 3 AND status = 'PUBLISHED';

COMMIT;
