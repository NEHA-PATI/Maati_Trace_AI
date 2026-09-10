BEGIN;

-- Versioned farmer-facing copy for calculated crop-intelligence cards.
-- Formula logic remains in the feature engine; this table only controls names,
-- ranges, wording, and signal explanations.
CREATE TABLE IF NOT EXISTS public.crop_intelligence_metric_content (
    content_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_code text NOT NULL DEFAULT '*',
    metric_key text NOT NULL,
    content_version text NOT NULL,
    display_name text NOT NULL,
    signal_meaning text NOT NULL,
    ranges jsonb NOT NULL DEFAULT '{}'::jsonb,
    messages jsonb NOT NULL DEFAULT '{}'::jsonb,
    field_interpretation jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    is_active boolean NOT NULL DEFAULT false,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    updated_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_metric_content_version UNIQUE (crop_code, metric_key, content_version)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_metric_content_active
    ON public.crop_intelligence_metric_content(crop_code, metric_key)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_metric_content_public
    ON public.crop_intelligence_metric_content(crop_code, metric_key, status, is_active);

-- One global published baseline. Crop-specific rows can be added later and
-- override these rows without changing the calculation code.
INSERT INTO public.crop_intelligence_metric_content
    (crop_code, metric_key, content_version, display_name, signal_meaning, ranges, messages, field_interpretation, status, is_active, published_at)
VALUES
('*', 'crop_condition', 'global_v1', 'Crop Condition', 'A combined crop-health score. Higher values mean the crop signals are more supportive overall.', '{"condition":[{"min":80,"max":100,"status":"good","label":"Good","rangeText":"80 to 100"},{"min":60,"max":79.999,"status":"fair","label":"Fair","rangeText":"60 to 79"},{"min":40,"max":59.999,"status":"attention","label":"Needs attention","rangeText":"40 to 59"},{"min":20,"max":39.999,"status":"poor","label":"Poor","rangeText":"20 to 39"},{"min":0,"max":19.999,"status":"critical","label":"Critical","rangeText":"0 to 19"}]}', '{}', '{"allGood":"The calculated crop signals look stable overall right now.","multiIssueLead":"A few calculated crop signals need a closer look. ","maxIssues":3}', 'published', true, now()),
('*', 'water_stress', 'global_v1', 'Water Stress Risk', 'Evidence that the crop may be short of usable water, using canopy moisture, root-zone moisture, rainfall, heat, evapotranspiration, and radar signals.', '{"risk":[{"min":0,"max":19.999,"status":"normal","label":"Normal","rangeText":"0 to 19"},{"min":20,"max":39.999,"status":"watch","label":"Watch","rangeText":"20 to 39"},{"min":40,"max":59.999,"status":"attention","label":"Attention","rangeText":"40 to 59"},{"min":60,"max":79.999,"status":"high","label":"High","rangeText":"60 to 79"},{"min":80,"max":100,"status":"critical","label":"Critical","rangeText":"80 to 100"}]}', '{}', '{}', 'published', true, now()),
('*', 'moisture_condition', 'global_v1', 'Crop Moisture', 'The current moisture condition around the crop, combining canopy and root-zone moisture observations.', '{"condition":[{"min":80,"max":100,"status":"good","label":"Good","rangeText":"80 to 100"},{"min":60,"max":79.999,"status":"fair","label":"Fair","rangeText":"60 to 79"},{"min":40,"max":59.999,"status":"attention","label":"Needs attention","rangeText":"40 to 59"},{"min":20,"max":39.999,"status":"poor","label":"Poor","rangeText":"20 to 39"},{"min":0,"max":19.999,"status":"critical","label":"Critical","rangeText":"0 to 19"}]}', '{}', '{}', 'published', true, now()),
('*', 'growth_condition', 'global_v1', 'Growth Condition', 'How supportive the observed vegetation level and growth direction are for the selected crop.', '{"condition":[{"min":80,"max":100,"status":"good","label":"Good","rangeText":"80 to 100"},{"min":60,"max":79.999,"status":"fair","label":"Fair","rangeText":"60 to 79"},{"min":40,"max":59.999,"status":"attention","label":"Needs attention","rangeText":"40 to 59"},{"min":20,"max":39.999,"status":"poor","label":"Poor","rangeText":"20 to 39"},{"min":0,"max":19.999,"status":"critical","label":"Critical","rangeText":"0 to 19"}]}', '{}', '{}', 'published', true, now()),
('*', 'growth_anomaly', 'global_v1', 'Growth Anomaly', 'How unusual the current crop growth is compared with its recent history, nearby H3 cells, and expected trajectory.', '{"risk":[{"min":0,"max":19.999,"status":"normal","label":"Normal","rangeText":"0 to 19"},{"min":20,"max":39.999,"status":"watch","label":"Watch","rangeText":"20 to 39"},{"min":40,"max":59.999,"status":"attention","label":"Attention","rangeText":"40 to 59"},{"min":60,"max":79.999,"status":"high","label":"High","rangeText":"60 to 79"},{"min":80,"max":100,"status":"critical","label":"Critical","rangeText":"80 to 100"}]}', '{}', '{}', 'published', true, now()),
('*', 'heat_stress', 'global_v1', 'Heat Stress Risk', 'Evidence of heat load on the crop from H3-level thermal observations and atmospheric demand.', '{"risk":[{"min":0,"max":19.999,"status":"normal","label":"Normal","rangeText":"0 to 19"},{"min":20,"max":39.999,"status":"watch","label":"Watch","rangeText":"20 to 39"},{"min":40,"max":59.999,"status":"attention","label":"Attention","rangeText":"40 to 59"},{"min":60,"max":79.999,"status":"high","label":"High","rangeText":"60 to 79"},{"min":80,"max":100,"status":"critical","label":"Critical","rangeText":"80 to 100"}]}', '{}', '{}', 'published', true, now()),
('*', 'waterlogging_risk', 'global_v1', 'Waterlogging Risk', 'Evidence of excess water or poor drainage from optical water, wet-soil, rainfall, terrain, historic water, and radar signals.', '{"risk":[{"min":0,"max":19.999,"status":"normal","label":"Normal","rangeText":"0 to 19"},{"min":20,"max":39.999,"status":"watch","label":"Watch","rangeText":"20 to 39"},{"min":40,"max":59.999,"status":"attention","label":"Attention","rangeText":"40 to 59"},{"min":60,"max":79.999,"status":"high","label":"High","rangeText":"60 to 79"},{"min":80,"max":100,"status":"critical","label":"Critical","rangeText":"80 to 100"}]}', '{}', '{}', 'published', true, now()),
('*', 'soil_condition', 'global_v1', 'Soil Condition', 'A modeled soil and terrain suitability signal using mapped soil properties and drainage context; it is not a laboratory test.', '{"condition":[{"min":80,"max":100,"status":"good","label":"Good","rangeText":"80 to 100"},{"min":60,"max":79.999,"status":"fair","label":"Fair","rangeText":"60 to 79"},{"min":40,"max":59.999,"status":"attention","label":"Needs attention","rangeText":"40 to 59"},{"min":20,"max":39.999,"status":"poor","label":"Poor","rangeText":"20 to 39"},{"min":0,"max":19.999,"status":"critical","label":"Critical","rangeText":"0 to 19"}]}', '{}', '{}', 'published', true, now()),
('*', 'nutrient_stress_risk', 'global_v1', 'Nutrient Stress Risk', 'Evidence that crop growth and mapped soil properties may be consistent with nutrient stress; it is not an N, P, or K diagnosis.', '{"risk":[{"min":0,"max":19.999,"status":"normal","label":"Normal","rangeText":"0 to 19"},{"min":20,"max":39.999,"status":"watch","label":"Watch","rangeText":"20 to 39"},{"min":40,"max":59.999,"status":"attention","label":"Attention","rangeText":"40 to 59"},{"min":60,"max":79.999,"status":"high","label":"High","rangeText":"60 to 79"},{"min":80,"max":100,"status":"critical","label":"Critical","rangeText":"80 to 100"}]}', '{}', '{}', 'published', true, now()),
('*', 'erosion_risk', 'global_v1', 'Land / Erosion Risk', 'Relative susceptibility to soil loss based mainly on terrain slope, land cover, soil context, and moisture conditions.', '{"risk":[{"min":0,"max":19.999,"status":"normal","label":"Normal","rangeText":"0 to 19"},{"min":20,"max":39.999,"status":"watch","label":"Watch","rangeText":"20 to 39"},{"min":40,"max":59.999,"status":"attention","label":"Attention","rangeText":"40 to 59"},{"min":60,"max":79.999,"status":"high","label":"High","rangeText":"60 to 79"},{"min":80,"max":100,"status":"critical","label":"Critical","rangeText":"80 to 100"}]}', '{}', '{}', 'published', true, now())
ON CONFLICT (crop_code, metric_key, content_version) DO NOTHING;

COMMIT;
