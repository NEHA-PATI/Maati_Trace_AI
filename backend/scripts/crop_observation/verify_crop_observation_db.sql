\pset pager off
\echo '=== final Crop Observation objects ==='
SELECT to_regclass('crop_observation.record_reviews') AS record_reviews,
       to_regclass('crop_observation.admin_audit_events') AS admin_audit_events,
       to_regclass('crop_observation.v_practice_records') AS v_practice_records;

\echo '=== media lifecycle columns ==='
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'crop_observation'
  AND ((table_name = 'media_assets' AND column_name = 'upload_expires_at')
    OR (table_name = 'system_media_assets' AND column_name IN ('upload_status', 'upload_expires_at')))
ORDER BY table_name, column_name;

\echo '=== stale upload tickets ==='
SELECT 'farmer' AS kind, count(*)
FROM crop_observation.media_assets
WHERE upload_status = 'REQUESTED'
  AND COALESCE(upload_expires_at, created_at + interval '15 minutes') <= now()
UNION ALL
SELECT 'system', count(*)
FROM crop_observation.system_media_assets
WHERE upload_status = 'REQUESTED'
  AND COALESCE(upload_expires_at, created_at + interval '15 minutes') <= now();
