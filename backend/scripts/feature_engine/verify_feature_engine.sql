-- Crop registration fields
SELECT column_name
FROM information_schema.columns
WHERE table_schema='public' AND table_name='farms'
  AND column_name IN ('crop_code','crop_name','crop_variety','crop_stage','planting_date')
ORDER BY column_name;

-- Active crop profiles (expect coconut / kala_jeera / mango)
SELECT crop_code, crop_name, profile_version, minimum_history_days,
       preferred_history_days, status, is_active
FROM crop_feature_profiles
ORDER BY crop_code, profile_version;

-- Formula registry (expect 10 per crop, 30 published+active)
SELECT crop_code, COUNT(*) AS formula_count,
       COUNT(*) FILTER (WHERE is_active) AS active_count
FROM crop_formula_registry
GROUP BY crop_code ORDER BY crop_code;

-- Component catalog (expect 41 rows)
SELECT COUNT(*) AS component_count FROM calculation_component_catalog WHERE is_active;

-- Latest engineered features
SELECT farm_id, feature_date, h3_index, crop_code, crop_profile_version, feature_version, confidence
FROM farm_h3_engineered_features
ORDER BY feature_date DESC, farm_id, h3_index
LIMIT 50;

-- Latest farm calculations
SELECT farm_id, result_date, prediction_key, score, status_label,
       confidence, affected_area_percent, formula_version
FROM farm_calculated_predictions
WHERE result_scope='farm'
ORDER BY result_date DESC, farm_id, prediction_key
LIMIT 50;

-- Latest display-grid calculated values
SELECT farm_id, result_date, grid_cell_id, prediction_key, score,
       confidence, contributing_h3_count, dominant_h3_index, value_source
FROM farm_grid_calculated_values
ORDER BY result_date DESC, farm_id, grid_cell_id, prediction_key
LIMIT 50;

-- Duplicate guards: each should return zero rows.
SELECT farm_id, h3_index, feature_date, feature_version, crop_profile_version, COUNT(*)
FROM farm_h3_engineered_features
GROUP BY farm_id, h3_index, feature_date, feature_version, crop_profile_version
HAVING COUNT(*) > 1;

SELECT farm_id, h3_index, result_date, prediction_key, formula_version, COUNT(*)
FROM farm_calculated_predictions
WHERE result_scope='h3'
GROUP BY farm_id, h3_index, result_date, prediction_key, formula_version
HAVING COUNT(*) > 1;
