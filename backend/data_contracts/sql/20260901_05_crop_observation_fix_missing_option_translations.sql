-- =============================================================================
-- crop_observation_service — 20260901_04 seeded practice_field_options for
-- Seed Management (seed_source) and Nursery Management (nursery_condition)
-- but never seeded practice_field_option_translations for them, so those
-- two fields rendered their raw option codes (e.g. "OWN_SAVED") instead of
-- a translated label. Fixes that.
--
-- Idempotent: safe to re-run.
-- =============================================================================

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'seed_management'
JOIN (VALUES
    ('OWN_SAVED', 'en-IN', 'My own saved seed'),
    ('OWN_SAVED', 'or-IN', 'ନିଜ ସାଠିରଖା ବିହନ'),
    ('MARKET_PURCHASED', 'en-IN', 'Bought from market'),
    ('MARKET_PURCHASED', 'or-IN', 'ବଜାରରୁ କିଣିଥିଲି'),
    ('GOVT_SUPPLIED', 'en-IN', 'Government supplied'),
    ('GOVT_SUPPLIED', 'or-IN', 'ସରକାରୀ ଯୋଗାଣ'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (field_option_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'nursery_management'
JOIN (VALUES
    ('GOOD', 'en-IN', 'Good'),
    ('GOOD', 'or-IN', 'ଭଲ ଅଛି'),
    ('AVERAGE', 'en-IN', 'Average'),
    ('AVERAGE', 'or-IN', 'ମଧ୍ୟମ'),
    ('POOR', 'en-IN', 'Poor'),
    ('POOR', 'or-IN', 'ଖରାପ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (field_option_id, locale) DO NOTHING;
