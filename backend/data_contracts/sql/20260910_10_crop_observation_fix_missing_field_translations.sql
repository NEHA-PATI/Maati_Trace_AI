-- Ensure every dynamic farmer field has labels in both supported languages.
-- Missing labels must not make an otherwise published crop screen unusable.

INSERT INTO crop_observation.practice_field_translations
    (field_definition_id, locale, label)
SELECT fd.field_definition_id, v.locale, v.label
FROM crop_observation.practice_field_definitions fd
JOIN (VALUES
    ('orchard_condition', 'en-IN', 'How is the orchard today?'),
    ('orchard_condition', 'or-IN', 'ଆଜି ବଗିଚା କେମିତି ଅଛି?'),
    ('input_category', 'en-IN', 'What type of input did you use?'),
    ('input_category', 'or-IN', 'କେଉଁ ପ୍ରକାରର ଇନପୁଟ ବ୍ୟବହାର କଲେ?'),
    ('product_code', 'en-IN', 'Which product did you use?'),
    ('product_code', 'or-IN', 'କେଉଁ ଉତ୍ପାଦ ବ୍ୟବହାର କଲେ?'),
    ('quantity', 'en-IN', 'How much did you use?'),
    ('quantity', 'or-IN', 'କେତେ ପରିମାଣ ବ୍ୟବହାର କଲେ?'),
    ('application_method', 'en-IN', 'How did you apply it?'),
    ('application_method', 'or-IN', 'କିପରି ପ୍ରୟୋଗ କଲେ?'),
    ('application_area', 'en-IN', 'Where did you apply it?'),
    ('application_area', 'or-IN', 'କେଉଁଠାରେ ପ୍ରୟୋଗ କଲେ?'),
    ('pest_observed', 'en-IN', 'Which pest did you see?'),
    ('pest_observed', 'or-IN', 'କେଉଁ ପୋକ ଦେଖିଲେ?'),
    ('disease_observed', 'en-IN', 'Which disease did you see?'),
    ('disease_observed', 'or-IN', 'କେଉଁ ରୋଗ ଦେଖିଲେ?'),
    ('severity', 'en-IN', 'How serious is it?'),
    ('severity', 'or-IN', 'କେତେ ଗୁରୁତର?'),
    ('control_method', 'en-IN', 'What did you do about it?'),
    ('control_method', 'or-IN', 'ଏହା ପାଇଁ କଣ କଲେ?'),
    ('damage_cause', 'en-IN', 'What caused the damage?'),
    ('damage_cause', 'or-IN', 'କ୍ଷତିର କାରଣ କଣ?'),
    ('harvest_method', 'en-IN', 'How did you harvest?'),
    ('harvest_method', 'or-IN', 'କେମିତି ଅମଳ କଲେ?'),
    ('quantity_harvested', 'en-IN', 'How much did you harvest?'),
    ('quantity_harvested', 'or-IN', 'କେତେ ଅମଳ ହେଲା?'),
    ('harvest_area', 'en-IN', 'What area was harvested?'),
    ('harvest_area', 'or-IN', 'କେଉଁ କ୍ଷେତ୍ରରୁ ଅମଳ କଲେ?'),
    ('drying_method', 'en-IN', 'How did you dry it?'),
    ('drying_method', 'or-IN', 'କିପରି ଶୁଖାଇଲେ?'),
    ('storage_method', 'en-IN', 'How did you store it?'),
    ('storage_method', 'or-IN', 'କିପରି ସଂରକ୍ଷଣ କଲେ?')
) AS v(field_code, locale, label)
    ON v.field_code = fd.field_code
ON CONFLICT (field_definition_id, locale) DO NOTHING;
