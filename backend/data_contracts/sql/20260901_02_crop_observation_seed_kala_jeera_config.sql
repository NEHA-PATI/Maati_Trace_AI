-- =============================================================================
-- crop_observation_service — seed a PUBLISHED v1 configuration for
-- kala_jeera so Phase 2 (observations, nutrient practice, screen API) has
-- something real to read/write against end to end.
--
-- Stage list and practice mapping follow the crop's own worked example
-- (an annual paddy-type crop: seedling -> vegetative -> panicle initiation
-- -> flowering -> grain filling -> ripening -> harvesting -> post harvest).
-- Odia translations here are a first pass for wiring, not final agronomist
-- copy — the admin config UI (Phase 4) is where those get reviewed/edited.
--
-- coconut / mango are intentionally left without a published configuration
-- for now — do not start a crop cycle for them until Phase 4 seeds/admin
-- authors their stage/practice sets.
--
-- Idempotent: safe to re-run.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Config version (v1, PUBLISHED)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.crop_config_versions (crop_id, version_number, status, published_at)
SELECT c.crop_id, 1, 'PUBLISHED', now()
FROM crop_observation.crops c
WHERE c.crop_code = 'kala_jeera'
ON CONFLICT (crop_id, version_number) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. Stages
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.crop_stages (config_version_id, stage_code, display_order, is_initial)
SELECT cv.config_version_id, v.stage_code, v.display_order, v.is_initial
FROM crop_observation.crop_config_versions cv
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
CROSS JOIN (VALUES
    ('seedling', 1, true),
    ('vegetative', 2, false),
    ('panicle_initiation', 3, false),
    ('flowering', 4, false),
    ('grain_filling', 5, false),
    ('ripening', 6, false),
    ('harvesting', 7, false),
    ('post_harvest', 8, false)
) AS v(stage_code, display_order, is_initial)
WHERE c.crop_code = 'kala_jeera' AND cv.version_number = 1
ON CONFLICT (config_version_id, stage_code) DO NOTHING;

INSERT INTO crop_observation.crop_stage_translations (stage_id, locale, display_name)
SELECT s.stage_id, v.locale, v.display_name
FROM crop_observation.crop_stages s
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('seedling', 'en-IN', 'Seedling'),
    ('seedling', 'or-IN', 'ଚାରା ଅବସ୍ଥା'),
    ('vegetative', 'en-IN', 'Vegetative Growth'),
    ('vegetative', 'or-IN', 'ବଢ଼ିବା ଅବସ୍ଥା'),
    ('panicle_initiation', 'en-IN', 'Panicle Initiation'),
    ('panicle_initiation', 'or-IN', 'ମଞ୍ଜରୀ ଆରମ୍ଭ'),
    ('flowering', 'en-IN', 'Flowering'),
    ('flowering', 'or-IN', 'ଫୁଲ ଅବସ୍ଥା'),
    ('grain_filling', 'en-IN', 'Grain Filling'),
    ('grain_filling', 'or-IN', 'ଦାନା ପୂରଣ'),
    ('ripening', 'en-IN', 'Ripening'),
    ('ripening', 'or-IN', 'ପାଚିବା ଅବସ୍ଥା'),
    ('harvesting', 'en-IN', 'Harvesting'),
    ('harvesting', 'or-IN', 'ଅମଳ'),
    ('post_harvest', 'en-IN', 'Post Harvest'),
    ('post_harvest', 'or-IN', 'ଅମଳ ପରେ')
) AS v(stage_code, locale, display_name)
    ON v.stage_code = s.stage_code
WHERE c.crop_code = 'kala_jeera' AND cv.version_number = 1
ON CONFLICT (stage_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 3. Practice template translations (shared across all crops)
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_translations (practice_template_id, locale, display_name)
SELECT pt.practice_template_id, v.locale, v.display_name
FROM crop_observation.practice_templates pt
JOIN (VALUES
    ('nutrient_management', 'en-IN', 'Nutrient Management'),
    ('nutrient_management', 'or-IN', 'ପୋଷକ ପରିଚାଳନା'),
    ('weed_management', 'en-IN', 'Weed Management'),
    ('weed_management', 'or-IN', 'ଘାସ ପରିଚାଳନା'),
    ('pest_management', 'en-IN', 'Pest Management'),
    ('pest_management', 'or-IN', 'କୀଟ ପରିଚାଳନା'),
    ('disease_management', 'en-IN', 'Disease Management'),
    ('disease_management', 'or-IN', 'ରୋଗ ପରିଚାଳନା'),
    ('harvest_management', 'en-IN', 'Harvest'),
    ('harvest_management', 'or-IN', 'ଅମଳ'),
    ('post_harvest', 'en-IN', 'Post Harvest'),
    ('post_harvest', 'or-IN', 'ଅମଳ ପରେ'),
    ('seed_management', 'en-IN', 'Seed Management'),
    ('seed_management', 'or-IN', 'ବିହନ ପରିଚାଳନା'),
    ('nursery_management', 'en-IN', 'Nursery Management'),
    ('nursery_management', 'or-IN', 'ନର୍ସରୀ ପରିଚାଳନା'),
    ('orchard_management', 'en-IN', 'Orchard Management'),
    ('orchard_management', 'or-IN', 'ବଗିଚା ପରିଚାଳନା'),
    ('crop_damage', 'en-IN', 'Crop Damage'),
    ('crop_damage', 'or-IN', 'ଫସଲ କ୍ଷତି')
) AS v(practice_code, locale, display_name)
    ON v.practice_code = pt.practice_code
ON CONFLICT (practice_template_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 4. Stage -> practice mapping for kala_jeera
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.stage_practices (stage_id, practice_template_id, display_order)
SELECT s.stage_id, pt.practice_template_id, v.display_order
FROM crop_observation.crop_stages s
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('seedling', 'seed_management', 1),
    ('seedling', 'nursery_management', 2),
    ('seedling', 'nutrient_management', 3),
    ('seedling', 'weed_management', 4),
    ('seedling', 'pest_management', 5),
    ('seedling', 'disease_management', 6),

    ('vegetative', 'nutrient_management', 1),
    ('vegetative', 'weed_management', 2),
    ('vegetative', 'pest_management', 3),
    ('vegetative', 'disease_management', 4),

    ('panicle_initiation', 'nutrient_management', 1),
    ('panicle_initiation', 'pest_management', 2),
    ('panicle_initiation', 'disease_management', 3),

    ('flowering', 'pest_management', 1),
    ('flowering', 'disease_management', 2),

    ('grain_filling', 'pest_management', 1),
    ('grain_filling', 'disease_management', 2),

    ('ripening', 'crop_damage', 1),
    ('ripening', 'pest_management', 2),
    ('ripening', 'disease_management', 3),

    ('harvesting', 'harvest_management', 1),

    ('post_harvest', 'post_harvest', 1)
) AS v(stage_code, practice_code, display_order)
    ON v.stage_code = s.stage_code
JOIN crop_observation.practice_templates pt ON pt.practice_code = v.practice_code
WHERE c.crop_code = 'kala_jeera' AND cv.version_number = 1
ON CONFLICT (stage_id, practice_template_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 5. Nutrient Management fields — seeded on every stage that carries the
--    practice (seedling, vegetative, panicle_initiation). This is the V1
--    field set from the product spec: input category, product, quantity,
--    application method, application area.
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt
    ON pt.practice_template_id = sp.practice_template_id AND pt.practice_code = 'nutrient_management'
CROSS JOIN (VALUES
    ('input_category', 'SINGLE_CHOICE', NULL, 1, true),
    ('product_code', 'SINGLE_CHOICE', NULL, 2, false),
    ('quantity', 'QUANTITY_UNIT', NULL, 3, true),
    ('application_method', 'SINGLE_CHOICE', NULL, 4, true),
    ('application_area', 'APPLICATION_AREA', 'TREATMENT_AREA_SCOPE', 5, true)
) AS v(field_code, field_type, semantic_type, display_order, is_required)
WHERE c.crop_code = 'kala_jeera'
  AND cv.version_number = 1
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation')
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('input_category', 'en-IN', 'What did you apply?'),
    ('input_category', 'or-IN', 'ଆପଣ କଣ ପ୍ରୟୋଗ କରିଥିଲେ?'),
    ('product_code', 'en-IN', 'Product'),
    ('product_code', 'or-IN', 'ଉତ୍ପାଦ'),
    ('quantity', 'en-IN', 'How much?'),
    ('quantity', 'or-IN', 'କେତେ ପରିମାଣ?'),
    ('application_method', 'en-IN', 'Application method'),
    ('application_method', 'or-IN', 'ପ୍ରୟୋଗ ପଦ୍ଧତି'),
    ('application_area', 'en-IN', 'Application Area'),
    ('application_area', 'or-IN', 'ପ୍ରୟୋଗ କ୍ଷେତ୍ର')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.version_number = 1
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation')
ON CONFLICT (field_definition_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 6. Options for the choice-style nutrient fields
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('input_category', 'CHEMICAL_FERTILIZER', 1),
    ('input_category', 'ORGANIC', 2),
    ('input_category', 'MICRONUTRIENT', 3),
    ('input_category', 'OTHER', 4),

    ('product_code', 'UREA', 1),
    ('product_code', 'DAP', 2),
    ('product_code', 'NPK', 3),
    ('product_code', 'OTHER', 4),

    ('application_method', 'BROADCAST', 1),
    ('application_method', 'SOIL', 2),
    ('application_method', 'FOLIAR', 3),
    ('application_method', 'OTHER', 4),

    ('application_area', 'WHOLE_FARM', 1),
    ('application_area', 'SELECTED_AREA', 2)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.version_number = 1
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation')
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('CHEMICAL_FERTILIZER', 'en-IN', 'Fertilizer'),
    ('CHEMICAL_FERTILIZER', 'or-IN', 'ସାର'),
    ('ORGANIC', 'en-IN', 'Organic'),
    ('ORGANIC', 'or-IN', 'ଜୈବିକ'),
    ('MICRONUTRIENT', 'en-IN', 'Micronutrient'),
    ('MICRONUTRIENT', 'or-IN', 'ଅଣୁପୋଷକ'),

    ('UREA', 'en-IN', 'Urea'),
    ('UREA', 'or-IN', 'ୟୁରିଆ'),
    ('DAP', 'en-IN', 'DAP'),
    ('DAP', 'or-IN', 'ଡିଏପି'),
    ('NPK', 'en-IN', 'NPK'),
    ('NPK', 'or-IN', 'ଏନପିକେ'),

    ('BROADCAST', 'en-IN', 'Broadcast'),
    ('BROADCAST', 'or-IN', 'ଛିଟାଇ'),
    ('SOIL', 'en-IN', 'Soil'),
    ('SOIL', 'or-IN', 'ମାଟିରେ'),
    ('FOLIAR', 'en-IN', 'Foliar'),
    ('FOLIAR', 'or-IN', 'ପତ୍ରରେ'),

    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ'),

    ('WHOLE_FARM', 'en-IN', 'Whole Farm'),
    ('WHOLE_FARM', 'or-IN', 'ସମ୍ପୂର୍ଣ୍ଣ ଜମି'),
    ('SELECTED_AREA', 'en-IN', 'Selected Area'),
    ('SELECTED_AREA', 'or-IN', 'ନିର୍ଦ୍ଦିଷ୍ଟ ଅଂଶ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.version_number = 1
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation')
ON CONFLICT (field_option_id, locale) DO NOTHING;
