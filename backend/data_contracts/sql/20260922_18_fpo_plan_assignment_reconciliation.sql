BEGIN;

-- Forward-only repair for assignments created before published plan version 2.
-- Move only stale assignments; explicitly pinned published versions remain unchanged.
UPDATE public.fpo_class_assignments a
SET configuration_version = latest.version
FROM (
    SELECT class_code, MAX(version) AS version
    FROM public.fpo_plan_versions
    WHERE status = 'PUBLISHED'
    GROUP BY class_code
) latest
WHERE a.class_code = latest.class_code
  AND a.is_active = TRUE
  AND NOT EXISTS (
      SELECT 1
      FROM public.fpo_plan_versions p
      WHERE p.class_code = a.class_code
        AND p.version = a.configuration_version
        AND p.status = 'PUBLISHED'
  );

COMMIT;
