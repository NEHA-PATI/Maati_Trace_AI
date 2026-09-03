-- =============================================================================
-- crop_observation_service — published starter configurations for coconut
-- and mango, plus richer pest/disease/product fields for all supported crops.
--
-- Research basis:
-- - Coconut main-field / nutrient / irrigation guidance from TNAU Agritech.
-- - Mango flowering / fruit-set / harvest maturity guidance from TNAU Agritech.
-- These are starter operational configs meant to make the admin and farmer
-- flows fully usable; agronomy copy can still be refined in admin.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Kala Jeera pest/disease fields: identify the actual issue and product.
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, NULL, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('pest_management', 'pest_observed', 'PEST', 1, true),
    ('pest_management', 'product_code', 'PRODUCT', 4, false),
    ('disease_management', 'disease_observed', 'DISEASE', 1, true),
    ('disease_management', 'product_code', 'PRODUCT', 4, false)
) AS v(practice_code, field_code, field_type, display_order, is_required)
    ON v.practice_code = pt.practice_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.status = 'PUBLISHED'
  AND s.stage_code IN ('seedling', 'vegetative', 'panicle_initiation', 'flowering', 'grain_filling', 'ripening')
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('pest_observed', 'en-IN', 'Which pest did you see?'),
    ('pest_observed', 'or-IN', 'କେଉଁ ପୋକ ଦେଖିଲେ?'),
    ('disease_observed', 'en-IN', 'Which disease did you see?'),
    ('disease_observed', 'or-IN', 'କେଉଁ ରୋଗ ଦେଖିଲେ?'),
    ('product_code', 'en-IN', 'Which product did you use?'),
    ('product_code', 'or-IN', 'କେଉଁ ଉତ୍ପାଦ ବ୍ୟବହାର କଲେ?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.status = 'PUBLISHED'
  AND fd.field_code IN ('pest_observed', 'disease_observed', 'product_code')
ON CONFLICT (field_definition_id, locale) DO NOTHING;

-- Common choice options for Kala Jeera pests/diseases/products.
INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('pest_observed', 'STEM_BORER', 1),
    ('pest_observed', 'BROWN_PLANTHOPPER', 2),
    ('pest_observed', 'LEAF_FOLDER', 3),
    ('pest_observed', 'NOT_SURE', 4),
    ('disease_observed', 'BLAST', 1),
    ('disease_observed', 'BLIGHT', 2),
    ('disease_observed', 'SHEATH_BLIGHT', 3),
    ('disease_observed', 'NOT_SURE', 4),
    ('product_code', 'CARBOFURAN', 1),
    ('product_code', 'IMIDACLOPRID', 2),
    ('product_code', 'COPPER_FUNGICIDE', 3),
    ('product_code', 'OTHER', 4)
) AS v(field_code, option_code, display_order)
    ON v.field_code = fd.field_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.status = 'PUBLISHED'
  AND fd.field_code IN ('pest_observed', 'disease_observed', 'product_code')
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, v.locale, v.label
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('STEM_BORER', 'en-IN', 'Stem borer'),
    ('STEM_BORER', 'or-IN', 'ଷ୍ଟେମ ବୋରର'),
    ('BROWN_PLANTHOPPER', 'en-IN', 'Brown planthopper'),
    ('BROWN_PLANTHOPPER', 'or-IN', 'ବ୍ରାଉନ ପ୍ଲାଣ୍ଟହପର'),
    ('LEAF_FOLDER', 'en-IN', 'Leaf folder'),
    ('LEAF_FOLDER', 'or-IN', 'ଲିଫ ଫୋଲ୍ଡର'),
    ('BLAST', 'en-IN', 'Blast'),
    ('BLAST', 'or-IN', 'ବ୍ଲାଷ୍ଟ'),
    ('BLIGHT', 'en-IN', 'Blight'),
    ('BLIGHT', 'or-IN', 'ବ୍ଲାଇଟ'),
    ('SHEATH_BLIGHT', 'en-IN', 'Sheath blight'),
    ('SHEATH_BLIGHT', 'or-IN', 'ଶିଥ ବ୍ଲାଇଟ'),
    ('NOT_SURE', 'en-IN', 'Not sure'),
    ('NOT_SURE', 'or-IN', 'ନିଶ୍ଚିତ ନୁହେଁ'),
    ('CARBOFURAN', 'en-IN', 'Carbofuran'),
    ('CARBOFURAN', 'or-IN', 'କାର୍ବୋଫୁରାନ'),
    ('IMIDACLOPRID', 'en-IN', 'Imidacloprid'),
    ('IMIDACLOPRID', 'or-IN', 'ଇମିଡାକ୍ଲୋପ୍ରିଡ'),
    ('COPPER_FUNGICIDE', 'en-IN', 'Copper fungicide'),
    ('COPPER_FUNGICIDE', 'or-IN', 'କପର ଫଂଗିସାଇଡ'),
    ('OTHER', 'en-IN', 'Other'),
    ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ')
) AS v(option_code, locale, label)
    ON v.option_code = fo.option_code
WHERE c.crop_code = 'kala_jeera'
  AND cv.status = 'PUBLISHED'
  AND fd.field_code IN ('pest_observed', 'disease_observed', 'product_code')
ON CONFLICT (field_option_id, locale) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. Coconut and mango published starter configs.
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.crop_config_versions (crop_id, version_number, status, published_at)
SELECT c.crop_id, 1, 'PUBLISHED', now()
FROM crop_observation.crops c
WHERE c.crop_code IN ('coconut', 'mango')
ON CONFLICT (crop_id, version_number) DO NOTHING;

INSERT INTO crop_observation.crop_stages (config_version_id, stage_code, display_order, is_initial)
SELECT cv.config_version_id, v.stage_code, v.display_order, v.is_initial
FROM crop_observation.crop_config_versions cv
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('coconut', 'establishment', 1, true),
    ('coconut', 'vegetative', 2, false),
    ('coconut', 'flowering', 3, false),
    ('coconut', 'nut_development', 4, false),
    ('coconut', 'harvesting', 5, false),
    ('mango', 'vegetative_flush', 1, true),
    ('mango', 'flowering', 2, false),
    ('mango', 'fruit_set', 3, false),
    ('mango', 'fruit_development', 4, false),
    ('mango', 'harvesting', 5, false),
    ('mango', 'post_harvest', 6, false)
) AS v(crop_code, stage_code, display_order, is_initial)
    ON v.crop_code = c.crop_code
WHERE cv.version_number = 1
ON CONFLICT (config_version_id, stage_code) DO NOTHING;

INSERT INTO crop_observation.crop_stage_translations (stage_id, locale, display_name, short_description, instruction_text)
SELECT s.stage_id, v.locale, v.display_name, v.short_description, v.instruction_text
FROM crop_observation.crop_stages s
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('coconut', 'establishment', 'en-IN', 'Establishment', 'Young palms establish roots and canopy.', 'Track planting health, irrigation, and first nutrient support.'),
    ('coconut', 'establishment', 'or-IN', 'ସ୍ଥାପନ', 'ନୂଆ ଗଛ ମୂଳ ଓ ପତ୍ର ଗଠନ କରୁଛି।', 'ରୋପଣ ପରବର୍ତ୍ତୀ ସ୍ୱାସ୍ଥ୍ୟ, ପାଣି ଓ ପ୍ରଥମ ପୋଷକ ଧ୍ୟାନରେ ରଖନ୍ତୁ।'),
    ('coconut', 'vegetative', 'en-IN', 'Vegetative', 'Palm is expanding leaves and stem.', 'Watch leaf colour, irrigation, and orchard upkeep.'),
    ('coconut', 'vegetative', 'or-IN', 'ବୃଦ୍ଧି ଅବସ୍ଥା', 'ଗଛ ପତ୍ର ଓ ତଣ୍ଟ ବୃଦ୍ଧି କରୁଛି।', 'ପତ୍ରର ରଙ୍ଗ, ପାଣି ଓ ବଗିଚା ପରିଚାଳନା ଧ୍ୟାନରେ ରଖନ୍ତୁ।'),
    ('coconut', 'flowering', 'en-IN', 'Flowering', 'Inflorescence and female flowers are active.', 'Note flowering intensity, pests, and timely nutrition.'),
    ('coconut', 'flowering', 'or-IN', 'ଫୁଲ ଅବସ୍ଥା', 'ଗଛରେ ଫୁଲ ଓ ଫଳାଣ ପ୍ରକ୍ରିୟା ଚାଲିଛି।', 'ଫୁଲର ଅବସ୍ଥା, ପୋକ ଓ ପୋଷକ ନିୟମିତ ଦେଖନ୍ତୁ।'),
    ('coconut', 'nut_development', 'en-IN', 'Nut Development', 'Tender and mature nuts are developing.', 'Track nut set, water stress, and damage.'),
    ('coconut', 'nut_development', 'or-IN', 'ନଡ଼ିଆ ବିକାଶ', 'ନଡ଼ିଆ ଫଳ ଗଠନ ଓ ବିକାଶ ହେଉଛି।', 'ଫଳ ଧରା, ଜଳ ଅଭାବ ଓ କ୍ଷତି ଦେଖନ୍ତୁ।'),
    ('coconut', 'harvesting', 'en-IN', 'Harvesting', 'Harvest-ready bunches are being collected.', 'Record harvest method, quantity, and visible losses.'),
    ('coconut', 'harvesting', 'or-IN', 'ଅମଳ', 'ପକ୍କା ଗୁଛା ସଂଗ୍ରହ କରାଯାଉଛି।', 'ଅମଳ ପ୍ରକ୍ରିୟା, ପରିମାଣ ଓ କ୍ଷତି ଲେଖନ୍ତୁ।'),
    ('mango', 'vegetative_flush', 'en-IN', 'Vegetative Flush', 'New shoots and canopy are flushing.', 'Track orchard health, nutrition, and disease early.'),
    ('mango', 'vegetative_flush', 'or-IN', 'ପତ୍ର ବୃଦ୍ଧି', 'ନୂତନ ପତ୍ର ଓ ଶାଖା ବୃଦ୍ଧି ହେଉଛି।', 'ବଗିଚା ସ୍ୱାସ୍ଥ୍ୟ, ପୋଷକ ଓ ଆରମ୍ଭିକ ରୋଗ ଦେଖନ୍ତୁ।'),
    ('mango', 'flowering', 'en-IN', 'Flowering', 'Panicles and blooms are active.', 'Observe bloom health, pest pressure, and sprays.'),
    ('mango', 'flowering', 'or-IN', 'ଫୁଲ ଅବସ୍ଥା', 'ମଞ୍ଜରୀ ଓ ଫୁଲ ଦେଖାଯାଉଛି।', 'ଫୁଲର ସ୍ୱାସ୍ଥ୍ୟ, ପୋକ ଚାପ ଓ ଛିଟାଇ ଦେଖନ୍ତୁ।'),
    ('mango', 'fruit_set', 'en-IN', 'Fruit Set', 'Small fruits are setting and retaining.', 'Track fruit drop, nutrition, and disease signs.'),
    ('mango', 'fruit_set', 'or-IN', 'ଫଳ ଧରା', 'ଛୋଟ ଫଳ ଧରୁଛି ଓ ଟିକି ରହୁଛି।', 'ଫଳ ଝରା, ପୋଷକ ଓ ରୋଗ ସଙ୍କେତ ଦେଖନ୍ତୁ।'),
    ('mango', 'fruit_development', 'en-IN', 'Fruit Development', 'Fruits are filling and maturing.', 'Watch size, colour, pests, and orchard water needs.'),
    ('mango', 'fruit_development', 'or-IN', 'ଫଳ ବିକାଶ', 'ଫଳ ଭରୁଛି ଓ ପକ୍କା ହେଉଛି।', 'ଆକାର, ରଙ୍ଗ, ପୋକ ଓ ପାଣି ଆବଶ୍ୟକତା ଦେଖନ୍ତୁ।'),
    ('mango', 'harvesting', 'en-IN', 'Harvesting', 'Mature fruits are being picked.', 'Record harvest timing, method, and yield.'),
    ('mango', 'harvesting', 'or-IN', 'ଅମଳ', 'ପକ୍କା ଫଳ ସଂଗ୍ରହ କରାଯାଉଛି।', 'ଅମଳ ସମୟ, ପ୍ରକ୍ରିୟା ଓ ଉତ୍ପାଦନ ଲେଖନ୍ତୁ।'),
    ('mango', 'post_harvest', 'en-IN', 'Post Harvest', 'Sorting, storage, and market preparation.', 'Track grading, storage, and post-harvest handling.'),
    ('mango', 'post_harvest', 'or-IN', 'ଅମଳ ପରେ', 'ଛାଟାଇ, ସଞ୍ଚୟ ଓ ବଜାର ପାଇଁ ପ୍ରସ୍ତୁତି।', 'ଗ୍ରେଡିଙ୍ଗ, ସଞ୍ଚୟ ଓ ପରଅମଳ ପରିଚାଳନା ଲେଖନ୍ତୁ।')
) AS v(crop_code, stage_code, locale, display_name, short_description, instruction_text)
    ON v.crop_code = c.crop_code AND v.stage_code = s.stage_code
WHERE cv.version_number = 1
ON CONFLICT (stage_id, locale) DO NOTHING;

INSERT INTO crop_observation.stage_practices (stage_id, practice_template_id, display_order, media_config)
SELECT s.stage_id, pt.practice_template_id, v.display_order, v.media_config::jsonb
FROM crop_observation.crop_stages s
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN crop_observation.practice_templates pt ON true
JOIN (VALUES
    ('coconut', 'establishment', 'orchard_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'establishment', 'nutrient_management', 2, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'vegetative', 'orchard_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'vegetative', 'nutrient_management', 2, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'vegetative', 'pest_management', 3, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'vegetative', 'disease_management', 4, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'flowering', 'nutrient_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'flowering', 'pest_management', 2, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'flowering', 'disease_management', 3, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'nut_development', 'crop_damage', 1, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'nut_development', 'pest_management', 2, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('coconut', 'harvesting', 'harvest_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'vegetative_flush', 'orchard_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'vegetative_flush', 'nutrient_management', 2, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'flowering', 'pest_management', 1, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'flowering', 'disease_management', 2, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'fruit_set', 'nutrient_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'fruit_set', 'crop_damage', 2, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'fruit_development', 'pest_management', 1, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'fruit_development', 'disease_management', 2, '{"issue_evidence":{"enabled":true,"max_images":2,"required":false},"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'harvesting', 'harvest_management', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}'),
    ('mango', 'post_harvest', 'post_harvest', 1, '{"practice_evidence":{"enabled":true,"max_images":2,"required":false},"voice_note":{"enabled":true,"max_count":1,"max_seconds":60}}')
) AS v(crop_code, stage_code, practice_code, display_order, media_config)
    ON v.crop_code = c.crop_code AND v.stage_code = s.stage_code AND v.practice_code = pt.practice_code
WHERE cv.version_number = 1
ON CONFLICT (stage_id, practice_template_id) DO NOTHING;

-- Reuse generic field shapes so the current frontend can render everything.
INSERT INTO crop_observation.practice_field_definitions
    (stage_practice_id, field_code, field_type, semantic_type, display_order, is_required)
SELECT sp.stage_practice_id, v.field_code, v.field_type, v.semantic_type, v.display_order, v.is_required
FROM crop_observation.stage_practices sp
JOIN crop_observation.practice_templates pt ON pt.practice_template_id = sp.practice_template_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
    ('orchard_management', 'orchard_condition', 'SINGLE_CHOICE', NULL, 1, true),
    ('nutrient_management', 'input_category', 'SINGLE_CHOICE', NULL, 1, true),
    ('nutrient_management', 'product_code', 'PRODUCT', NULL, 2, false),
    ('nutrient_management', 'quantity', 'QUANTITY_UNIT', NULL, 3, true),
    ('nutrient_management', 'application_method', 'SINGLE_CHOICE', NULL, 4, true),
    ('nutrient_management', 'application_area', 'APPLICATION_AREA', 'TREATMENT_AREA_SCOPE', 5, true),
    ('pest_management', 'pest_observed', 'PEST', NULL, 1, true),
    ('pest_management', 'severity', 'SINGLE_CHOICE', NULL, 2, true),
    ('pest_management', 'control_method', 'SINGLE_CHOICE', NULL, 3, true),
    ('pest_management', 'product_code', 'PRODUCT', NULL, 4, false),
    ('pest_management', 'quantity', 'QUANTITY_UNIT', NULL, 5, false),
    ('disease_management', 'disease_observed', 'DISEASE', NULL, 1, true),
    ('disease_management', 'severity', 'SINGLE_CHOICE', NULL, 2, true),
    ('disease_management', 'control_method', 'SINGLE_CHOICE', NULL, 3, true),
    ('disease_management', 'product_code', 'PRODUCT', NULL, 4, false),
    ('disease_management', 'quantity', 'QUANTITY_UNIT', NULL, 5, false),
    ('crop_damage', 'damage_cause', 'SINGLE_CHOICE', NULL, 1, true),
    ('crop_damage', 'severity', 'SINGLE_CHOICE', NULL, 2, true),
    ('harvest_management', 'harvest_method', 'SINGLE_CHOICE', NULL, 1, true),
    ('harvest_management', 'quantity_harvested', 'QUANTITY_UNIT', NULL, 2, true),
    ('harvest_management', 'harvest_area', 'APPLICATION_AREA', 'TREATMENT_AREA_SCOPE', 3, true),
    ('post_harvest', 'drying_method', 'SINGLE_CHOICE', NULL, 1, false),
    ('post_harvest', 'storage_method', 'SINGLE_CHOICE', NULL, 2, true)
) AS v(practice_code, field_code, field_type, semantic_type, display_order, is_required)
    ON v.practice_code = pt.practice_code
WHERE c.crop_code IN ('coconut', 'mango')
  AND cv.version_number = 1
ON CONFLICT (stage_practice_id, field_code) DO NOTHING;

-- Simple translations and options for new crops.
INSERT INTO crop_observation.practice_field_translations (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN (VALUES
    ('orchard_condition', 'en-IN', 'How is the orchard today?'),
    ('orchard_condition', 'or-IN', 'ଆଜି ବଗିଚା କେମିତି ଅଛି?'),
    ('pest_observed', 'en-IN', 'Which pest did you see?'),
    ('pest_observed', 'or-IN', 'କେଉଁ ପୋକ ଦେଖିଲେ?'),
    ('disease_observed', 'en-IN', 'Which disease did you see?'),
    ('disease_observed', 'or-IN', 'କେଉଁ ରୋଗ ଦେଖିଲେ?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
ON CONFLICT (field_definition_id, locale) DO NOTHING;
