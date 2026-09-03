-- =============================================================================
-- crop_observation_service — field definitions for every kala_jeera practice
-- that 20260901_02 mapped to a stage but never gave configurable fields to
-- (only nutrient_management had fields). Until now every other "Today's
-- Activities" button (Weed, Pest, Disease, Harvest, Post Harvest, Seed,
-- Nursery, Crop Damage) was permanently disabled in the farmer UI, because
-- validate_practice_answers() 409s on a practice with zero field
-- definitions and the frontend disables a button with fields.length === 0.
--
-- Every field below reuses field_types the farmer UI already renders
-- (SINGLE_CHOICE, QUANTITY_UNIT, APPLICATION_AREA) — no new frontend
-- component is required to unblock these.
--
-- Idempotent: safe to re-run.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Seed Management (seedling)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'seed_management'
CROSS JOIN (VALUES
    ('seed_source', 'SINGLE_CHOICE', NULL, 1, true),
    ('quantity', 'QUANTITY_UNIT', NULL, 2, false)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'seed_management'
JOIN (VALUES
    ('seed_source', 'en-IN', 'Where did the seed come from?'),
    ('seed_source', 'or-IN', 'ବିହନ କେଉଁଠାରୁ ଆସିଲା?'),
    ('quantity', 'en-IN', 'How much seed used?'),
    ('quantity', 'or-IN', 'କେତେ ବିହନ ବ୍ୟବହାର ହେଲା?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'seed_management'
JOIN (VALUES
    ('seed_source', 'OWN_SAVED', 1),
    ('seed_source', 'MARKET_PURCHASED', 2),
    ('seed_source', 'GOVT_SUPPLIED', 3),
    ('seed_source', 'OTHER', 4)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Nursery Management (seedling)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'nursery_management'
CROSS JOIN (VALUES
    ('nursery_condition', 'SINGLE_CHOICE', NULL, 1, true)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'nursery_management'
JOIN (VALUES
    ('nursery_condition', 'en-IN', 'How is the nursery looking?'),
    ('nursery_condition', 'or-IN', 'ନର୍ସରୀ କେମିତି ଅଛି?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'nursery_management'
JOIN (VALUES
    ('nursery_condition', 'GOOD', 1),
    ('nursery_condition', 'AVERAGE', 2),
    ('nursery_condition', 'POOR', 3)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'seedling'
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Weed Management (seedling, vegetative)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'weed_management'
CROSS JOIN (VALUES
    ('weed_method', 'SINGLE_CHOICE', NULL, 1, true),
    ('quantity', 'QUANTITY_UNIT', NULL, 2, false),
    ('application_area', 'APPLICATION_AREA', 'TREATMENT_AREA_SCOPE', 3, true)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code IN ('seedling', 'vegetative')
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'weed_management'
JOIN (VALUES
    ('weed_method', 'en-IN', 'How did you control weeds?'),
    ('weed_method', 'or-IN', 'ଘାସ କେମିତି ନିୟନ୍ତ୍ରଣ କଲେ?'),
    ('quantity', 'en-IN', 'How much herbicide (if any)?'),
    ('quantity', 'or-IN', 'କେତେ ଔଷଧ ବ୍ୟବହାର ହେଲା (ଯଦି)?'),
    ('application_area', 'en-IN', 'Application Area'),
    ('application_area', 'or-IN', 'ପ୍ରୟୋଗ କ୍ଷେତ୍ର')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code IN ('seedling', 'vegetative')
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'weed_management'
JOIN (VALUES
    ('weed_method', 'MANUAL', 1),
    ('weed_method', 'MECHANICAL', 2),
    ('weed_method', 'HERBICIDE', 3),
    ('weed_method', 'OTHER', 4),
    ('application_area', 'WHOLE_FARM', 1),
    ('application_area', 'SELECTED_AREA', 2)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code IN ('seedling', 'vegetative')
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'weed_management'
JOIN (VALUES
    ('MANUAL', 'en-IN', 'Manual (by hand)'),
    ('MANUAL', 'or-IN', 'ହାତରେ'),
    ('MECHANICAL', 'en-IN', 'Mechanical'),
    ('MECHANICAL', 'or-IN', 'ଯନ୍ତ୍ର ଦ୍ୱାରା'),
    ('HERBICIDE', 'en-IN', 'Herbicide (chemical)'),
    ('HERBICIDE', 'or-IN', 'ରାସାୟନିକ ଔଷଧ'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ'),
    ('WHOLE_FARM', 'en-IN', 'Whole Farm'),
    ('WHOLE_FARM', 'or-IN', 'ସମ୍ପୂର୍ଣ୍ଣ ଜମି'),
    ('SELECTED_AREA', 'en-IN', 'Selected Area'),
    ('SELECTED_AREA', 'or-IN', 'ନିର୍ଦ୍ଦିଷ୍ଟ ଅଂଶ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code IN ('seedling', 'vegetative')
ON CONFLICT (field_option_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Pest Management + Disease Management (seedling, vegetative,
-- panicle_initiation, flowering, grain_filling, ripening) — same field
-- shape for both, seeded together to halve the SQL.
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id
    AND pt.practice_code IN ('pest_management', 'disease_management')
CROSS JOIN (VALUES
    ('severity', 'SINGLE_CHOICE', NULL, 1, true),
    ('control_method', 'SINGLE_CHOICE', NULL, 2, true),
    ('quantity', 'QUANTITY_UNIT', NULL, 3, false)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED'
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation', 'flowering', 'grain_filling', 'ripening')
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id
    AND pt.practice_code IN ('pest_management', 'disease_management')
JOIN (VALUES
    ('severity', 'en-IN', 'How bad is it?'),
    ('severity', 'or-IN', 'କେତେ ଗୁରୁତର?'),
    ('control_method', 'en-IN', 'What did you do about it?'),
    ('control_method', 'or-IN', 'ଆପଣ କଣ କରିଥିଲେ?'),
    ('quantity', 'en-IN', 'How much product used?'),
    ('quantity', 'or-IN', 'କେତେ ଔଷଧ ବ୍ୟବହାର ହେଲା?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED'
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation', 'flowering', 'grain_filling', 'ripening')
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id
    AND pt.practice_code IN ('pest_management', 'disease_management')
JOIN (VALUES
    ('severity', 'LOW', 1),
    ('severity', 'MEDIUM', 2),
    ('severity', 'HIGH', 3),
    ('severity', 'NOT_SURE', 4),
    ('control_method', 'MANUAL', 1),
    ('control_method', 'BIOLOGICAL', 2),
    ('control_method', 'CHEMICAL', 3),
    ('control_method', 'NOT_SURE', 4),
    ('control_method', 'OTHER', 5)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED'
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation', 'flowering', 'grain_filling', 'ripening')
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id
    AND pt.practice_code IN ('pest_management', 'disease_management')
JOIN (VALUES
    ('LOW', 'en-IN', 'Low'),
    ('LOW', 'or-IN', 'ଅଳ୍ପ'),
    ('MEDIUM', 'en-IN', 'Medium'),
    ('MEDIUM', 'or-IN', 'ମଧ୍ୟମ'),
    ('HIGH', 'en-IN', 'High'),
    ('HIGH', 'or-IN', 'ଅଧିକ'),
    ('NOT_SURE', 'en-IN', 'Not sure'),
    ('NOT_SURE', 'or-IN', 'ନିଶ୍ଚିତ ନୁହେଁ'),
    ('MANUAL', 'en-IN', 'Manual (by hand)'),
    ('MANUAL', 'or-IN', 'ହାତରେ'),
    ('BIOLOGICAL', 'en-IN', 'Biological / organic'),
    ('BIOLOGICAL', 'or-IN', 'ଜୈବିକ'),
    ('CHEMICAL', 'en-IN', 'Chemical spray'),
    ('CHEMICAL', 'or-IN', 'ରାସାୟନିକ ସ୍ପ୍ରେ'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED'
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation', 'flowering', 'grain_filling', 'ripening')
ON CONFLICT (field_option_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Crop Damage (ripening)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'crop_damage'
CROSS JOIN (VALUES
    ('damage_cause', 'SINGLE_CHOICE', NULL, 1, true),
    ('severity', 'SINGLE_CHOICE', NULL, 2, true)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'ripening'
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'crop_damage'
JOIN (VALUES
    ('damage_cause', 'en-IN', 'What caused the damage?'),
    ('damage_cause', 'or-IN', 'କ୍ଷତିର କାରଣ କଣ?'),
    ('severity', 'en-IN', 'How bad is it?'),
    ('severity', 'or-IN', 'କେତେ ଗୁରୁତର?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'ripening'
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'crop_damage'
JOIN (VALUES
    ('damage_cause', 'WEATHER', 1),
    ('damage_cause', 'ANIMAL', 2),
    ('damage_cause', 'PEST', 3),
    ('damage_cause', 'OTHER', 4),
    ('severity', 'LOW', 1),
    ('severity', 'MEDIUM', 2),
    ('severity', 'HIGH', 3)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'ripening'
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'crop_damage'
JOIN (VALUES
    ('WEATHER', 'en-IN', 'Weather'),
    ('WEATHER', 'or-IN', 'ପାଣିପାଗ'),
    ('ANIMAL', 'en-IN', 'Animal'),
    ('ANIMAL', 'or-IN', 'ପଶୁ'),
    ('PEST', 'en-IN', 'Pest'),
    ('PEST', 'or-IN', 'କୀଟ'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ'),
    ('LOW', 'en-IN', 'Low'),
    ('LOW', 'or-IN', 'ଅଳ୍ପ'),
    ('MEDIUM', 'en-IN', 'Medium'),
    ('MEDIUM', 'or-IN', 'ମଧ୍ୟମ'),
    ('HIGH', 'en-IN', 'High'),
    ('HIGH', 'or-IN', 'ଅଧିକ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'ripening'
ON CONFLICT (field_option_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Harvest Management (harvesting)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'harvest_management'
CROSS JOIN (VALUES
    ('harvest_method', 'SINGLE_CHOICE', NULL, 1, true),
    ('quantity_harvested', 'QUANTITY_UNIT', NULL, 2, true),
    ('harvest_area', 'APPLICATION_AREA', 'TREATMENT_AREA_SCOPE', 3, true)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'harvesting'
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'harvest_management'
JOIN (VALUES
    ('harvest_method', 'en-IN', 'How did you harvest?'),
    ('harvest_method', 'or-IN', 'ଆପଣ କେମିତି ଅମଳ କଲେ?'),
    ('quantity_harvested', 'en-IN', 'How much harvested?'),
    ('quantity_harvested', 'or-IN', 'କେତେ ଅମଳ ହେଲା?'),
    ('harvest_area', 'en-IN', 'Harvest Area'),
    ('harvest_area', 'or-IN', 'ଅମଳ କ୍ଷେତ୍ର')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'harvesting'
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'harvest_management'
JOIN (VALUES
    ('harvest_method', 'MANUAL', 1),
    ('harvest_method', 'MECHANICAL', 2),
    ('harvest_method', 'OTHER', 3),
    ('harvest_area', 'WHOLE_FARM', 1),
    ('harvest_area', 'SELECTED_AREA', 2)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'harvesting'
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'harvest_management'
JOIN (VALUES
    ('MANUAL', 'en-IN', 'Manual (by hand)'),
    ('MANUAL', 'or-IN', 'ହାତରେ'),
    ('MECHANICAL', 'en-IN', 'Mechanical'),
    ('MECHANICAL', 'or-IN', 'ଯନ୍ତ୍ର ଦ୍ୱାରା'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ'),
    ('WHOLE_FARM', 'en-IN', 'Whole Farm'),
    ('WHOLE_FARM', 'or-IN', 'ସମ୍ପୂର୍ଣ୍ଣ ଜମି'),
    ('SELECTED_AREA', 'en-IN', 'Selected Area'),
    ('SELECTED_AREA', 'or-IN', 'ନିର୍ଦ୍ଦିଷ୍ଟ ଅଂଶ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'harvesting'
ON CONFLICT (field_option_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Post Harvest (post_harvest)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'post_harvest'
CROSS JOIN (VALUES
    ('drying_method', 'SINGLE_CHOICE', NULL, 1, true),
    ('storage_method', 'SINGLE_CHOICE', NULL, 2, true)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'post_harvest'
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'post_harvest'
JOIN (VALUES
    ('drying_method', 'en-IN', 'How was it dried?'),
    ('drying_method', 'or-IN', 'କେମିତି ଶୁଖାଗଲା?'),
    ('storage_method', 'en-IN', 'How is it being stored?'),
    ('storage_method', 'or-IN', 'କେମିତି ସାଠିରଖା ଯାଉଛି?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'post_harvest'
ON CONFLICT (field_definition_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'post_harvest'
JOIN (VALUES
    ('drying_method', 'SUN_DRYING', 1),
    ('drying_method', 'MACHINE_DRYING', 2),
    ('drying_method', 'OTHER', 3),
    ('storage_method', 'GUNNY_BAG', 1),
    ('storage_method', 'SILO', 2),
    ('storage_method', 'WAREHOUSE', 3),
    ('storage_method', 'OTHER', 4)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'post_harvest'
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'post_harvest'
JOIN (VALUES
    ('SUN_DRYING', 'en-IN', 'Sun drying'),
    ('SUN_DRYING', 'or-IN', 'ବଉଦରେ ଶୁଖାଇବା'),
    ('MACHINE_DRYING', 'en-IN', 'Machine drying'),
    ('MACHINE_DRYING', 'or-IN', 'ଯନ୍ତ୍ରରେ ଶୁଖାଇବା'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ'),
    ('GUNNY_BAG', 'en-IN', 'Gunny bags'),
    ('GUNNY_BAG', 'or-IN', 'ଚଟ ବସ୍ତା'),
    ('SILO', 'en-IN', 'Silo'),
    ('SILO', 'or-IN', 'ସାଇଲୋ'),
    ('WAREHOUSE', 'en-IN', 'Warehouse'),
    ('WAREHOUSE', 'or-IN', 'ଗୋଦାମ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera' AND cv.status = 'PUBLISHED' AND s.stage_code = 'post_harvest'
ON CONFLICT (field_option_id, locale) DO NOTHING;
