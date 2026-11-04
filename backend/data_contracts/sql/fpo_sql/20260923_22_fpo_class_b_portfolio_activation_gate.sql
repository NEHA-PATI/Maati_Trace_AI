BEGIN;
-- B3/B4 capabilities are persisted and API-gated; Class B v3 remains draft until B8.
UPDATE public.fpo_feature_catalogue SET is_active = TRUE, updated_at = now()
WHERE feature_key IN ('FARMER_SEGMENTATION','FARMER_NOTES_AND_FOLLOWUPS','SEASON_PLANNING','FIELD_ACTIVITY_PLANNING');
COMMIT;
