-- Seed the basic mango observation choices used by the starter configuration.
-- Idempotent: safe to run after the configuration has already been cloned.

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
  ('orchard_condition', 'GOOD', 1), ('orchard_condition', 'AVERAGE', 2), ('orchard_condition', 'POOR', 3),
  ('input_category', 'CHEMICAL_FERTILIZER', 1), ('input_category', 'ORGANIC', 2), ('input_category', 'MICRONUTRIENT', 3), ('input_category', 'OTHER', 4),
  ('product_code', 'UREA', 1), ('product_code', 'DAP', 2), ('product_code', 'NPK', 3), ('product_code', 'OTHER', 4),
  ('application_method', 'BROADCAST', 1), ('application_method', 'SOIL', 2), ('application_method', 'FOLIAR', 3), ('application_method', 'OTHER', 4),
  ('pest_observed', 'MANGO_HOPPER', 1), ('pest_observed', 'FRUIT_FLY', 2), ('pest_observed', 'MEALYBUG', 3), ('pest_observed', 'OTHER', 4),
  ('disease_observed', 'ANTHRACNOSE', 1), ('disease_observed', 'POWDERY_MILDEW', 2), ('disease_observed', 'DIEBACK', 3), ('disease_observed', 'OTHER', 4),
  ('severity', 'LOW', 1), ('severity', 'MEDIUM', 2), ('severity', 'HIGH', 3), ('severity', 'NOT_SURE', 4),
  ('control_method', 'MANUAL', 1), ('control_method', 'BIOLOGICAL', 2), ('control_method', 'CHEMICAL', 3), ('control_method', 'NOT_SURE', 4), ('control_method', 'OTHER', 5),
  ('damage_cause', 'WEATHER', 1), ('damage_cause', 'ANIMAL', 2), ('damage_cause', 'PEST', 3), ('damage_cause', 'OTHER', 4),
  ('harvest_method', 'HAND_PICKED', 1), ('harvest_method', 'PICKING_TOOL', 2), ('harvest_method', 'OTHER', 3),
  ('drying_method', 'SUN_DRYING', 1), ('drying_method', 'SHADE_DRYING', 2), ('drying_method', 'OTHER', 3),
  ('storage_method', 'ROOM_STORAGE', 1), ('storage_method', 'COLD_STORAGE', 2), ('storage_method', 'OTHER', 3)
) AS v(field_code, option_code, display_order) ON v.field_code = fd.field_code
WHERE c.crop_code = 'mango'
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
  ('GOOD', 'en-IN', 'Good'), ('GOOD', 'or-IN', 'ଭଲ'), ('AVERAGE', 'en-IN', 'Average'), ('AVERAGE', 'or-IN', 'ମଧ୍ୟମ'), ('POOR', 'en-IN', 'Poor'), ('POOR', 'or-IN', 'ଖରାପ'),
  ('CHEMICAL_FERTILIZER', 'en-IN', 'Chemical fertilizer'), ('CHEMICAL_FERTILIZER', 'or-IN', 'ରାସାୟନିକ ସାର'), ('ORGANIC', 'en-IN', 'Organic'), ('ORGANIC', 'or-IN', 'ଜୈବିକ'), ('MICRONUTRIENT', 'en-IN', 'Micronutrient'), ('MICRONUTRIENT', 'or-IN', 'ଅଣୁପୋଷକ'),
  ('UREA', 'en-IN', 'Urea'), ('UREA', 'or-IN', 'ୟୁରିଆ'), ('DAP', 'en-IN', 'DAP'), ('DAP', 'or-IN', 'ଡିଏପି'), ('NPK', 'en-IN', 'NPK'), ('NPK', 'or-IN', 'ଏନପିକେ'),
  ('BROADCAST', 'en-IN', 'Broadcast'), ('BROADCAST', 'or-IN', 'ଛିଟାଇ'), ('SOIL', 'en-IN', 'Soil application'), ('SOIL', 'or-IN', 'ମାଟିରେ ପ୍ରୟୋଗ'), ('FOLIAR', 'en-IN', 'Foliar spray'), ('FOLIAR', 'or-IN', 'ପତ୍ରରେ ପ୍ରୟୋଗ'),
  ('MANGO_HOPPER', 'en-IN', 'Mango hopper'), ('MANGO_HOPPER', 'or-IN', 'ଆମ୍ବ ହପର'), ('FRUIT_FLY', 'en-IN', 'Fruit fly'), ('FRUIT_FLY', 'or-IN', 'ଫଳ ମାଛି'), ('MEALYBUG', 'en-IN', 'Mealybug'), ('MEALYBUG', 'or-IN', 'ମିଲିବଗ'),
  ('ANTHRACNOSE', 'en-IN', 'Anthracnose'), ('ANTHRACNOSE', 'or-IN', 'ଆନ୍ଥ୍ରାକ୍ନୋଜ'), ('POWDERY_MILDEW', 'en-IN', 'Powdery mildew'), ('POWDERY_MILDEW', 'or-IN', 'ପାଉଡରି ମିଲଡିଉ'), ('DIEBACK', 'en-IN', 'Dieback'), ('DIEBACK', 'or-IN', 'ଡାଇବ୍ୟାକ'),
  ('LOW', 'en-IN', 'Low'), ('LOW', 'or-IN', 'କମ'), ('MEDIUM', 'en-IN', 'Medium'), ('MEDIUM', 'or-IN', 'ମଧ୍ୟମ'), ('HIGH', 'en-IN', 'High'), ('HIGH', 'or-IN', 'ଅଧିକ'), ('NOT_SURE', 'en-IN', 'Not sure'), ('NOT_SURE', 'or-IN', 'ଜଣାନାହିଁ'),
  ('MANUAL', 'en-IN', 'Manual'), ('MANUAL', 'or-IN', 'ହାତରେ'), ('BIOLOGICAL', 'en-IN', 'Biological'), ('BIOLOGICAL', 'or-IN', 'ଜୈବିକ'), ('CHEMICAL', 'en-IN', 'Chemical'), ('CHEMICAL', 'or-IN', 'ରାସାୟନିକ'),
  ('WEATHER', 'en-IN', 'Weather'), ('WEATHER', 'or-IN', 'ପାଣିପାଗ'), ('ANIMAL', 'en-IN', 'Animal'), ('ANIMAL', 'or-IN', 'ପଶୁ'), ('PEST', 'en-IN', 'Pest'), ('PEST', 'or-IN', 'ପୋକ'),
  ('HAND_PICKED', 'en-IN', 'Hand picked'), ('HAND_PICKED', 'or-IN', 'ହାତରେ ତୋଳା'), ('PICKING_TOOL', 'en-IN', 'Picking tool'), ('PICKING_TOOL', 'or-IN', 'ତୋଳା ଉପକରଣ'),
  ('SUN_DRYING', 'en-IN', 'Sun drying'), ('SUN_DRYING', 'or-IN', 'ଖରାରେ ଶୁଖାଇବା'), ('SHADE_DRYING', 'en-IN', 'Shade drying'), ('SHADE_DRYING', 'or-IN', 'ଛାଇରେ ଶୁଖାଇବା'),
  ('ROOM_STORAGE', 'en-IN', 'Room storage'), ('ROOM_STORAGE', 'or-IN', 'ଘରେ ସଞ୍ଚୟ'), ('COLD_STORAGE', 'en-IN', 'Cold storage'), ('COLD_STORAGE', 'or-IN', 'ଶୀତଳ ଭଣ୍ଡାର'),
  ('OTHER', 'en-IN', 'Other'), ('OTHER', 'or-IN', 'ଅନ୍ୟାନ୍ୟ')
) AS v(option_code, locale, label) ON v.option_code = fo.option_code
WHERE c.crop_code = 'mango'
ON CONFLICT (field_option_id, locale) DO NOTHING;

-- Reuse the bundled stage images for already-created mango drafts. Admins can
-- replace these images later without changing the default data.
INSERT INTO crop_observation.system_media_bindings
    (asset_id, target_type, target_id, asset_role, locale, slot_number, is_active)
SELECT source_binding.asset_id, 'STAGE', draft_stage.stage_id, 'STAGE_IMAGE', NULL, NULL, true
FROM crop_observation.crop_config_versions draft_config
JOIN crop_observation.crops c ON c.crop_id = draft_config.crop_id
JOIN crop_observation.crop_stages draft_stage ON draft_stage.config_version_id = draft_config.config_version_id
JOIN crop_observation.crop_config_versions published_config ON published_config.crop_id = c.crop_id AND published_config.status = 'PUBLISHED'
JOIN crop_observation.crop_stages published_stage ON published_stage.config_version_id = published_config.config_version_id AND published_stage.stage_code = draft_stage.stage_code
JOIN crop_observation.system_media_bindings source_binding
  ON source_binding.target_type = 'STAGE' AND source_binding.target_id = published_stage.stage_id
 AND source_binding.asset_role = 'STAGE_IMAGE' AND source_binding.is_active = true
WHERE c.crop_code = 'mango' AND draft_config.status = 'DRAFT'
ON CONFLICT DO NOTHING;
