-- Seed the basic Coconut observation choices for every configuration version.
-- Idempotent: safe to run after configurations have been cloned.

INSERT INTO crop_observation.practice_field_options (field_definition_id, option_code, display_order)
SELECT fd.field_definition_id, v.option_code, v.display_order
FROM crop_observation.practice_field_definitions fd
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
JOIN (VALUES
  ('orchard_condition','GOOD',1),('orchard_condition','AVERAGE',2),('orchard_condition','POOR',3),
  ('input_category','CHEMICAL_FERTILIZER',1),('input_category','ORGANIC',2),('input_category','MICRONUTRIENT',3),('input_category','OTHER',4),
  ('product_code','UREA',1),('product_code','DAP',2),('product_code','NPK',3),('product_code','OTHER',4),
  ('application_method','BROADCAST',1),('application_method','SOIL',2),('application_method','FOLIAR',3),('application_method','OTHER',4),
  ('pest_observed','RED_PALM_WEEVIL',1),('pest_observed','RHYNOCOCCUS_SCALE',2),('pest_observed','RATS',3),('pest_observed','OTHER',4),
  ('disease_observed','BUD_ROT',1),('disease_observed','STEM_BLEEDING',2),('disease_observed','LEAF_SPOT',3),('disease_observed','OTHER',4),
  ('severity','LOW',1),('severity','MEDIUM',2),('severity','HIGH',3),('severity','NOT_SURE',4),
  ('control_method','MANUAL',1),('control_method','BIOLOGICAL',2),('control_method','CHEMICAL',3),('control_method','NOT_SURE',4),('control_method','OTHER',5),
  ('damage_cause','WEATHER',1),('damage_cause','ANIMAL',2),('damage_cause','PEST',3),('damage_cause','OTHER',4),
  ('harvest_method','HAND_PICKED',1),('harvest_method','PICKING_TOOL',2),('harvest_method','OTHER',3)
) AS v(field_code, option_code, display_order) ON v.field_code = fd.field_code
WHERE c.crop_code = 'coconut'
ON CONFLICT (field_definition_id, option_code) DO NOTHING;

INSERT INTO crop_observation.practice_field_option_translations (field_option_id, locale, label)
SELECT fo.field_option_id, locale.locale,
       initcap(replace(lower(fo.option_code), '_', ' '))
FROM crop_observation.practice_field_options fo
JOIN crop_observation.practice_field_definitions fd ON fd.field_definition_id = fo.field_definition_id
JOIN crop_observation.stage_practices sp ON sp.stage_practice_id = fd.stage_practice_id
JOIN crop_observation.crop_stages s ON s.stage_id = sp.stage_id
JOIN crop_observation.crop_config_versions cv ON cv.config_version_id = s.config_version_id
JOIN crop_observation.crops c ON c.crop_id = cv.crop_id
CROSS JOIN (VALUES ('en-IN'), ('or-IN')) AS locale(locale)
WHERE c.crop_code = 'coconut'
ON CONFLICT (field_option_id, locale) DO NOTHING;
