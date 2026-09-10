BEGIN;

-- MaatiTrace deterministic crop intelligence / feature-engine foundation.
-- Builds on the existing source observation tables. Does not alter Sentinel-2 processing.

ALTER TABLE public.farms
    ADD COLUMN IF NOT EXISTS crop_code text,
    ADD COLUMN IF NOT EXISTS crop_name text,
    ADD COLUMN IF NOT EXISTS crop_variety text,
    ADD COLUMN IF NOT EXISTS crop_stage text,
    ADD COLUMN IF NOT EXISTS planting_date date;

CREATE INDEX IF NOT EXISTS idx_farms_crop_code ON public.farms(crop_code);

-- Correct legacy display-grid rows that were populated by averaging Sentinel-2
-- SWIR reflectance into a field named surface_temp_c. Sentinel-2 is not thermal.
-- Crop heat features now use real Landsat C2 L2 surface temperature.
UPDATE public.farm_grid_daily_values
SET surface_temp_c = NULL,
    updated_at = now()
WHERE surface_temp_c IS NOT NULL
  AND COALESCE(value_source, 'unknown') IN ('h3_grid_overlap_weighted', 'unknown');

CREATE TABLE IF NOT EXISTS public.calculation_component_catalog (
    component_key text PRIMARY KEY,
    display_name text NOT NULL,
    category text NOT NULL,
    output_direction text NOT NULL CHECK (output_direction IN ('risk', 'condition')),
    description text NOT NULL,
    required_feature_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_groups jsonb NOT NULL DEFAULT '[]'::jsonb,
    implementation_version text NOT NULL DEFAULT 'component_v1',
    admin_selectable boolean NOT NULL DEFAULT true,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.crop_feature_profiles (
    profile_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_code text NOT NULL,
    crop_name text NOT NULL,
    profile_version text NOT NULL,
    crop_type text NOT NULL DEFAULT 'crop',
    minimum_history_days integer NOT NULL DEFAULT 60 CHECK (minimum_history_days >= 0),
    preferred_history_days integer NOT NULL DEFAULT 180 CHECK (preferred_history_days >= minimum_history_days),
    temporal_windows jsonb NOT NULL DEFAULT '{}'::jsonb,
    root_zone_weights jsonb NOT NULL DEFAULT '{}'::jsonb,
    soil_ranges jsonb NOT NULL DEFAULT '{}'::jsonb,
    normalization jsonb NOT NULL DEFAULT '{}'::jsonb,
    growth_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    is_active boolean NOT NULL DEFAULT false,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    updated_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_crop_feature_profile_version UNIQUE (crop_code, profile_version)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_crop_feature_profile_active
    ON public.crop_feature_profiles(crop_code)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_crop_feature_profiles_status
    ON public.crop_feature_profiles(crop_code, status, is_active);

CREATE TABLE IF NOT EXISTS public.crop_formula_registry (
    formula_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_code text NOT NULL,
    prediction_key text NOT NULL,
    display_name text NOT NULL,
    formula_version text NOT NULL,
    crop_profile_version text NOT NULL,
    formula_type text NOT NULL DEFAULT 'weighted_components'
        CHECK (formula_type IN ('weighted_components')),
    score_direction text NOT NULL CHECK (score_direction IN ('risk', 'condition')),
    execution_order integer NOT NULL DEFAULT 100,
    component_weights jsonb NOT NULL DEFAULT '{}'::jsonb,
    thresholds jsonb NOT NULL DEFAULT '{}'::jsonb,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    description text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    is_active boolean NOT NULL DEFAULT false,
    created_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    updated_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_crop_formula_version UNIQUE (crop_code, prediction_key, formula_version)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_crop_formula_active
    ON public.crop_formula_registry(crop_code, prediction_key)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_crop_formula_registry_lookup
    ON public.crop_formula_registry(crop_code, execution_order, is_active);

CREATE TABLE IF NOT EXISTS public.crop_configuration_audit (
    audit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    entity_type text NOT NULL,
    entity_id uuid,
    action text NOT NULL,
    before_state jsonb,
    after_state jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_crop_configuration_audit_created
    ON public.crop_configuration_audit(created_at DESC);

CREATE TABLE IF NOT EXISTS public.farm_h3_engineered_features (
    engineered_feature_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id uuid NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    farmer_id uuid NOT NULL REFERENCES public.farmer_profiles(farmer_id),
    fpo_id uuid REFERENCES public.fpos(fpo_id),
    h3_index bigint NOT NULL,
    h3_resolution integer NOT NULL,
    feature_date date NOT NULL,
    crop_code text NOT NULL,
    crop_profile_version text NOT NULL,
    feature_version text NOT NULL,
    anchor_dataset text NOT NULL DEFAULT 'sentinel_2_l2a',
    anchor_scene_id text,
    observed_area_m2 double precision,
    anchor_valid_fraction double precision,
    confidence double precision,
    features jsonb NOT NULL DEFAULT '{}'::jsonb,
    quality jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_dates jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_versions jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_h3_engineered_feature UNIQUE
      (farm_id, h3_index, feature_date, feature_version, crop_profile_version)
);

CREATE INDEX IF NOT EXISTS idx_farm_h3_engineered_features_farm_date
    ON public.farm_h3_engineered_features(farm_id, feature_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_h3_engineered_features_h3_date
    ON public.farm_h3_engineered_features(h3_index, feature_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_h3_engineered_features_crop
    ON public.farm_h3_engineered_features(crop_code, feature_date DESC);

CREATE TABLE IF NOT EXISTS public.farm_calculated_predictions (
    prediction_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id uuid NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    farmer_id uuid NOT NULL REFERENCES public.farmer_profiles(farmer_id),
    fpo_id uuid REFERENCES public.fpos(fpo_id),
    h3_index bigint,
    h3_resolution integer,
    result_scope text NOT NULL CHECK (result_scope IN ('h3', 'farm')),
    result_date date NOT NULL,
    crop_code text NOT NULL,
    prediction_key text NOT NULL,
    display_name text NOT NULL,
    score double precision,
    score_direction text NOT NULL CHECK (score_direction IN ('risk', 'condition')),
    status_label text NOT NULL,
    confidence double precision NOT NULL DEFAULT 0,
    affected_area_percent double precision,
    formula_version text NOT NULL,
    crop_profile_version text NOT NULL,
    feature_version text NOT NULL,
    components jsonb NOT NULL DEFAULT '{}'::jsonb,
    evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    quality jsonb NOT NULL DEFAULT '{}'::jsonb,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_farm_h3_calculated_prediction
    ON public.farm_calculated_predictions
      (farm_id, h3_index, result_date, prediction_key, formula_version)
    WHERE result_scope = 'h3' AND h3_index IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_farm_calculated_prediction
    ON public.farm_calculated_predictions
      (farm_id, result_date, prediction_key, formula_version)
    WHERE result_scope = 'farm' AND h3_index IS NULL;
CREATE INDEX IF NOT EXISTS idx_farm_calculated_predictions_latest
    ON public.farm_calculated_predictions(farm_id, result_scope, result_date DESC);

CREATE TABLE IF NOT EXISTS public.farm_grid_calculated_values (
    grid_calculation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id uuid NOT NULL REFERENCES public.farms(farm_id) ON DELETE CASCADE,
    grid_cell_id uuid NOT NULL REFERENCES public.farm_grid_cells(grid_cell_id) ON DELETE CASCADE,
    result_date date NOT NULL,
    crop_code text NOT NULL,
    prediction_key text NOT NULL,
    display_name text NOT NULL,
    score double precision,
    score_direction text NOT NULL CHECK (score_direction IN ('risk', 'condition')),
    status_label text NOT NULL,
    confidence double precision NOT NULL DEFAULT 0,
    formula_version text NOT NULL,
    crop_profile_version text NOT NULL,
    feature_version text NOT NULL,
    value_source text NOT NULL DEFAULT 'h3_formula_grid_overlap_weighted',
    contributing_h3_count integer NOT NULL DEFAULT 0,
    dominant_h3_index bigint,
    max_h3_overlap_ratio double precision,
    components jsonb NOT NULL DEFAULT '{}'::jsonb,
    evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_farm_grid_calculated_value UNIQUE
      (farm_id, grid_cell_id, result_date, prediction_key, formula_version)
);

CREATE INDEX IF NOT EXISTS idx_farm_grid_calculated_latest
    ON public.farm_grid_calculated_values(farm_id, result_date DESC, prediction_key);

-- Component catalog. These keys are backed by safe, versioned Python implementations;
-- administrators may choose/configure them but cannot execute arbitrary code.
INSERT INTO public.calculation_component_catalog
(component_key, display_name, category, output_direction, description, required_feature_keys, source_groups)
VALUES
('canopy_moisture_stress','Canopy moisture stress','water','risk','NDMI/MSI anomaly based canopy moisture stress evidence','["ndmi_z","msi_z"]','["sentinel2"]'),
('canopy_moisture_condition','Canopy moisture condition','water','condition','Inverse of canopy moisture stress','["ndmi_z","msi_z"]','["sentinel2"]'),
('rootzone_moisture_stress','Root-zone moisture stress','water','risk','SMAP and ERA5 root-zone soil-moisture anomaly evidence','["smap_rootzone_z","era5_rootzone_z"]','["smap","era5"]'),
('rootzone_moisture_condition','Root-zone moisture condition','water','condition','Inverse of root-zone moisture stress','["smap_rootzone_z","era5_rootzone_z"]','["smap","era5"]'),
('rainfall_stress','Rainfall deficit stress','water','risk','Crop-window rainfall anomaly plus rainfall deficit','["rain_window_z","rain_window_deficit"]','["gpm"]'),
('thermal_stress','Thermal stress','heat','risk','Landsat surface-temperature and ERA5 skin-temperature anomaly evidence','["surface_temp_z","era5_skin_temp_z"]','["landsat","era5"]'),
('lst_stress','Land surface temperature stress','heat','risk','Landsat surface-temperature anomaly evidence','["surface_temp_z"]','["landsat"]'),
('air_temperature_stress','Air temperature stress','heat','risk','ERA5 maximum-temperature anomaly evidence','["era5_temp_max_z"]','["era5"]'),
('et_deficit_stress','Evapotranspiration deficit','water','risk','One minus ET/PET ratio, clipped to 0-1','["et_pet_ratio"]','["modis_et"]'),
('atmospheric_demand_stress','Atmospheric drying demand','heat','risk','VPD normalized against crop-profile thresholds','["forecast_vpd"]','["forecast"]'),
('et0_stress','Reference ET demand','heat','risk','ET0 normalized against crop-profile thresholds','["forecast_et0_mm"]','["forecast"]'),
('sar_anomaly','SAR anomaly','radar','risk','Absolute Sentinel-1 VH/VV temporal anomaly','["sar_ratio_z"]','["sentinel1"]'),
('sar_condition','SAR condition','radar','condition','Inverse of SAR anomaly','["sar_ratio_z"]','["sentinel1"]'),
('vegetation_condition','Vegetation condition','growth','condition','NDVI, EVI, NIRv and LAI condition relative to history','["ndvi_z","evi_z","nirv_z","lai_z"]','["sentinel2","modis_vegetation"]'),
('growth_trend_condition','Growth trend condition','growth','condition','Canopy trend condition based on normalized temporal slopes','["ndvi_slope","evi_slope","nirv_slope","lai_slope"]','["sentinel2","modis_vegetation"]'),
('growth_trajectory_condition','Historical trajectory condition','growth','condition','Observed canopy position relative to historical trajectory baseline','["ndvi_trajectory_deviation"]','["sentinel2"]'),
('moisture_support_condition','Moisture support condition','growth','condition','Canopy/root-zone moisture support for growth','["ndmi_z","smap_rootzone_z","era5_rootzone_z"]','["sentinel2","smap","era5"]'),
('climate_support_condition','Climate support condition','growth','condition','Rainfall and thermal support for current growth','["rain_window_z","surface_temp_z","era5_temp_max_z"]','["gpm","landsat","era5"]'),
('temporal_anomaly','Temporal anomaly','anomaly','risk','Magnitude of vegetation/moisture anomalies against history','["ndvi_z","evi_z","nirv_z","ndmi_z","ndre_z"]','["sentinel2"]'),
('spatial_anomaly','Spatial anomaly','anomaly','risk','Robust deviation of H3 vegetation/moisture values from same-date farm peers','["spatial_ndvi_z","spatial_ndmi_z","spatial_nirv_z"]','["sentinel2"]'),
('environmental_stress_evidence','Environmental stress evidence','anomaly','risk','Combined water, heat and root-zone environmental stress evidence','["ndmi_z","rain_window_z","surface_temp_z","smap_rootzone_z","era5_rootzone_z"]','["sentinel2","gpm","landsat","smap","era5"]'),
('growth_trajectory_anomaly','Growth trajectory anomaly','anomaly','risk','Absolute deviation from historical crop trajectory','["ndvi_trajectory_deviation"]','["sentinel2"]'),
('optical_water_signal','Optical water signal','waterlogging','risk','MNDWI/NDWI high anomaly signal','["mndwi_z","ndwi_z"]','["sentinel2"]'),
('wet_soil_signal','Wet soil signal','waterlogging','risk','SMAP/ERA5 high soil-moisture anomaly','["smap_rootzone_z","era5_rootzone_z"]','["smap","era5"]'),
('rain_excess','Rainfall excess','waterlogging','risk','Positive crop-window rainfall anomaly','["rain_window_z"]','["gpm"]'),
('ponding_terrain','Ponding terrain','waterlogging','risk','Low-slope ponding susceptibility','["mean_slope_deg"]','["terrain"]'),
('historic_water_context','Historical water context','waterlogging','risk','JRC occurrence/permanent-water context','["water_occurrence_pct","jrc_permanent_water_fraction"]','["jrc_water"]'),
('soil_ph_suitability','Soil pH suitability','soil','condition','Crop-profile trapezoid suitability for SoilGrids pH','["soil_phh2o"]','["soilgrids"]'),
('soil_soc_suitability','Soil organic carbon support','soil','condition','Crop-profile normalized SOC support','["soil_soc"]','["soilgrids"]'),
('soil_cec_suitability','Soil CEC support','soil','condition','Crop-profile normalized cation-exchange capacity support','["soil_cec"]','["soilgrids"]'),
('soil_bulk_density_suitability','Bulk density suitability','soil','condition','Crop-profile bulk-density suitability','["soil_bdod"]','["soilgrids"]'),
('soil_texture_suitability','Soil texture suitability','soil','condition','Crop-profile clay/sand/silt suitability','["soil_clay","soil_sand","soil_silt"]','["soilgrids"]'),
('drainage_suitability','Drainage suitability','soil','condition','Crop-profile terrain/water-context drainage suitability','["mean_slope_deg","water_occurrence_pct"]','["terrain","jrc_water"]'),
('optical_nutrient_stress','Optical nutrient-stress signal','nutrition','risk','Low NDRE, RECI and GNDVI anomaly evidence','["ndre_z","reci_z","gndvi_z"]','["sentinel2"]'),
('soil_nutrient_stress','Soil nutrient-support stress','nutrition','risk','Low modeled nitrogen/SOC/CEC plus pH unsuitability','["soil_nitrogen","soil_soc","soil_cec","soil_phh2o"]','["soilgrids"]'),
('growth_nutrient_stress','Growth nutrient evidence','nutrition','risk','Low NIRv/EVI condition supporting nutrient-stress suspicion','["nirv_z","evi_z"]','["sentinel2"]'),
('terrain_erosion_risk','Terrain erosion susceptibility','erosion','risk','Slope-based erosion susceptibility proxy','["mean_slope_deg"]','["terrain"]'),
('bare_exposure','Bare/exposed land signal','erosion','risk','BSI anomaly, inverse FVC and WorldCover bare fraction','["bsi_z","fvc_proxy","bare_sparse_fraction"]','["sentinel2","landcover"]'),
('rain_erosivity_proxy','Rain erosivity proxy','erosion','risk','Heavy/recent rainfall anomaly proxy; not full RUSLE R','["rain_7d_z"]','["gpm"]'),
('soil_erodibility_proxy','Soil erodibility proxy','erosion','risk','Relative texture/SOC erodibility proxy; not laboratory K factor','["soil_silt","soil_sand","soil_soc"]','["soilgrids"]')
ON CONFLICT (component_key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    category = EXCLUDED.category,
    output_direction = EXCLUDED.output_direction,
    description = EXCLUDED.description,
    required_feature_keys = EXCLUDED.required_feature_keys,
    source_groups = EXCLUDED.source_groups,
    updated_at = now();

-- Initial crop profiles. These are transparent engineering defaults and must be calibrated
-- using field observations; metadata intentionally records that status.
INSERT INTO public.crop_feature_profiles
(crop_code, crop_name, profile_version, crop_type, minimum_history_days, preferred_history_days,
 temporal_windows, root_zone_weights, soil_ranges, normalization, growth_config, metadata,
 status, is_active, published_at)
VALUES
('coconut','Coconut','coconut_v1','perennial',90,365,
 '{"rainfall":[30,60,90],"vegetation":[30,60,90],"moisture":[30,60],"thermal":[14,30],"sar":[30,60],"primary_rainfall_window":60,"primary_growth_window":60}'::jsonb,
 '{"soil_water_0_7":0.10,"soil_water_7_28":0.20,"soil_water_28_100":0.40,"soil_water_100_289":0.30}'::jsonb,
 '{"phh2o":[4.5,5.5,7.0,8.0],"bdod":[0.8,1.0,1.5,1.8],"clay":[8,15,50,70],"sand":[10,20,65,85],"silt":[5,10,55,75],"slope_deg":[0,0.5,12,25]}'::jsonb,
 '{"z_critical":3.0,"vpd_low":0.8,"vpd_high":2.8,"et0_low":3.0,"et0_high":8.0,"ponding_slope_low":0.2,"ponding_slope_high":4.0,"erosion_slope_low":2.0,"erosion_slope_high":20.0,"soc_low":5.0,"soc_good":20.0,"cec_low":5.0,"cec_good":25.0,"nitrogen_low":0.3,"nitrogen_good":1.5,"trajectory_critical":0.30,"slope_decline_scale":0.01,"drainage_mode":"well_drained"}'::jsonb,
 '{"trajectory_mode":"historical_robust_median","stage_aware":false}'::jsonb,
 '{"validation_status":"engineering_default_requires_field_calibration"}'::jsonb,
 'published',true,now()),
('kala_jeera','Kala Jeera (Black Rice)','kala_jeera_v1','seasonal',60,180,
 '{"rainfall":[3,7,14,30],"vegetation":[14,30],"moisture":[7,14,30],"thermal":[7,14],"sar":[12,24],"primary_rainfall_window":14,"primary_growth_window":30}'::jsonb,
 '{"soil_water_0_7":0.35,"soil_water_7_28":0.40,"soil_water_28_100":0.25,"soil_water_100_289":0.00}'::jsonb,
 '{"phh2o":[4.5,5.5,7.0,8.0],"bdod":[0.8,1.0,1.5,1.8],"clay":[15,25,60,75],"sand":[5,10,45,70],"silt":[10,20,60,80],"slope_deg":[0,0,2,6]}'::jsonb,
 '{"z_critical":3.0,"vpd_low":0.8,"vpd_high":2.5,"et0_low":3.0,"et0_high":7.0,"ponding_slope_low":0.1,"ponding_slope_high":3.0,"erosion_slope_low":1.0,"erosion_slope_high":12.0,"soc_low":5.0,"soc_good":20.0,"cec_low":5.0,"cec_good":25.0,"nitrogen_low":0.3,"nitrogen_good":1.5,"trajectory_critical":0.25,"slope_decline_scale":0.015,"drainage_mode":"retain_water"}'::jsonb,
 '{"trajectory_mode":"historical_robust_median","stage_aware":false,"future_requirement":"planting_date_and_growth_stage"}'::jsonb,
 '{"validation_status":"engineering_default_requires_field_calibration"}'::jsonb,
 'published',true,now()),
('mango','Mango','mango_v1','perennial',90,365,
 '{"rainfall":[14,30,60,90],"vegetation":[30,60,90],"moisture":[14,30,60],"thermal":[14,30],"sar":[30,60],"primary_rainfall_window":30,"primary_growth_window":60}'::jsonb,
 '{"soil_water_0_7":0.15,"soil_water_7_28":0.25,"soil_water_28_100":0.35,"soil_water_100_289":0.25}'::jsonb,
 '{"phh2o":[5.0,5.5,7.5,8.5],"bdod":[0.8,1.0,1.5,1.8],"clay":[8,15,45,65],"sand":[10,20,60,80],"silt":[5,10,50,70],"slope_deg":[0,0.5,10,22]}'::jsonb,
 '{"z_critical":3.0,"vpd_low":0.8,"vpd_high":2.8,"et0_low":3.0,"et0_high":8.0,"ponding_slope_low":0.2,"ponding_slope_high":4.0,"erosion_slope_low":2.0,"erosion_slope_high":20.0,"soc_low":5.0,"soc_good":20.0,"cec_low":5.0,"cec_good":25.0,"nitrogen_low":0.3,"nitrogen_good":1.5,"trajectory_critical":0.30,"slope_decline_scale":0.01,"drainage_mode":"well_drained"}'::jsonb,
 '{"trajectory_mode":"historical_robust_median","stage_aware":false,"future_requirement":"flowering_and_fruit_stage"}'::jsonb,
 '{"validation_status":"engineering_default_requires_field_calibration"}'::jsonb,
 'published',true,now())
ON CONFLICT (crop_code, profile_version) DO NOTHING;

-- Common threshold contracts.
-- risk: <20 normal, <40 watch, <60 attention, <80 high, otherwise critical.
-- condition: >=80 good, >=60 fair, >=40 attention, >=20 poor, otherwise critical.

INSERT INTO public.crop_formula_registry
(crop_code,prediction_key,display_name,formula_version,crop_profile_version,score_direction,execution_order,component_weights,thresholds,parameters,description,metadata,status,is_active,published_at)
VALUES
-- Coconut
('coconut','water_stress','Water Stress Risk','water_stress_coconut_v1','coconut_v1','risk',100,'{"canopy_moisture_stress":0.22,"rootzone_moisture_stress":0.22,"rainfall_stress":0.10,"thermal_stress":0.15,"et_deficit_stress":0.12,"atmospheric_demand_stress":0.09,"sar_anomaly":0.10}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{"rain_window_days":60}','Multi-source deterministic water-stress evidence score.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','moisture_condition','Crop Moisture Condition','moisture_condition_coconut_v1','coconut_v1','condition',200,'{"canopy_moisture_condition":0.40,"rootzone_moisture_condition":0.40,"sar_condition":0.20}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Current canopy/root-zone moisture condition.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','growth_condition','Canopy Growth Condition','growth_condition_coconut_v1','coconut_v1','condition',300,'{"vegetation_condition":0.30,"growth_trend_condition":0.30,"growth_trajectory_condition":0.15,"moisture_support_condition":0.15,"climate_support_condition":0.10}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Perennial canopy growth/vigor condition, not physical plant-size growth.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','growth_anomaly','Growth Anomaly','growth_anomaly_coconut_v1','coconut_v1','risk',400,'{"temporal_anomaly":0.40,"spatial_anomaly":0.20,"environmental_stress_evidence":0.25,"growth_trajectory_anomaly":0.15}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Temporal, spatial and trajectory anomaly score.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','heat_stress','Heat Stress Risk','heat_stress_coconut_v1','coconut_v1','risk',500,'{"lst_stress":0.40,"air_temperature_stress":0.20,"atmospheric_demand_stress":0.25,"et0_stress":0.15}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Thermal and atmospheric-demand risk.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','waterlogging_risk','Waterlogging / Excess Water Risk','waterlogging_coconut_v1','coconut_v1','risk',600,'{"optical_water_signal":0.20,"wet_soil_signal":0.20,"rain_excess":0.15,"ponding_terrain":0.20,"historic_water_context":0.15,"sar_anomaly":0.10}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{"rain_window_days":30}','Excess-water and poor-drainage evidence score.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','soil_condition','Soil Condition','soil_condition_coconut_v1','coconut_v1','condition',700,'{"soil_ph_suitability":0.20,"soil_soc_suitability":0.20,"soil_cec_suitability":0.15,"soil_bulk_density_suitability":0.10,"soil_texture_suitability":0.20,"drainage_suitability":0.15}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Modeled soil/terrain suitability context; not a laboratory soil test.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','nutrient_stress_risk','Nutrient Stress Risk','nutrient_stress_coconut_v1','coconut_v1','risk',800,'{"optical_nutrient_stress":0.35,"soil_nutrient_stress":0.45,"growth_nutrient_stress":0.20}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Possible nutrient-related stress evidence; does not diagnose N/P/K deficiency.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','erosion_risk','Land / Erosion Risk','erosion_coconut_v1','coconut_v1','risk',850,'{"terrain_erosion_risk":0.30,"bare_exposure":0.25,"rain_erosivity_proxy":0.20,"soil_erodibility_proxy":0.25}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Relative erosion susceptibility proxy; not full RUSLE soil-loss estimation.','{"validation_status":"engineering_default"}','published',true,now()),
('coconut','crop_condition','Overall Crop Condition','crop_condition_coconut_v1','coconut_v1','condition',900,'{"prediction:growth_condition":0.25,"prediction:moisture_condition":0.25,"prediction_inverse:heat_stress":0.15,"prediction_inverse:nutrient_stress_risk":0.15,"prediction_inverse:waterlogging_risk":0.10,"prediction:soil_condition":0.10}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Quality-aware overall crop condition built from preceding deterministic outputs.','{"validation_status":"engineering_default"}','published',true,now()),

-- Kala Jeera
('kala_jeera','water_stress','Water Stress Risk','water_stress_kala_jeera_v1','kala_jeera_v1','risk',100,'{"canopy_moisture_stress":0.24,"rootzone_moisture_stress":0.18,"rainfall_stress":0.20,"thermal_stress":0.10,"et_deficit_stress":0.06,"atmospheric_demand_stress":0.08,"sar_anomaly":0.14}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{"rain_window_days":14}','Short-cycle rice water-stress evidence score.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','moisture_condition','Crop Moisture Condition','moisture_condition_kala_jeera_v1','kala_jeera_v1','condition',200,'{"canopy_moisture_condition":0.45,"rootzone_moisture_condition":0.35,"sar_condition":0.20}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Current canopy/root-zone moisture condition.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','growth_condition','Crop Growth Condition','growth_condition_kala_jeera_v1','kala_jeera_v1','condition',300,'{"vegetation_condition":0.35,"growth_trend_condition":0.25,"growth_trajectory_condition":0.25,"moisture_support_condition":0.10,"climate_support_condition":0.05}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Vegetative/growth trajectory condition. Stage-aware curves are a future refinement.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','growth_anomaly','Growth Anomaly','growth_anomaly_kala_jeera_v1','kala_jeera_v1','risk',400,'{"temporal_anomaly":0.35,"spatial_anomaly":0.20,"environmental_stress_evidence":0.20,"growth_trajectory_anomaly":0.25}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Temporal, spatial and trajectory anomaly score.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','heat_stress','Heat Stress Risk','heat_stress_kala_jeera_v1','kala_jeera_v1','risk',500,'{"lst_stress":0.35,"air_temperature_stress":0.30,"atmospheric_demand_stress":0.20,"et0_stress":0.15}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Thermal and atmospheric-demand risk.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','waterlogging_risk','Waterlogging / Excess Water Risk','waterlogging_kala_jeera_v1','kala_jeera_v1','risk',600,'{"optical_water_signal":0.20,"wet_soil_signal":0.20,"rain_excess":0.25,"ponding_terrain":0.10,"historic_water_context":0.10,"sar_anomaly":0.15}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{"rain_window_days":7}','Excess-water evidence. Standing water can be normal for managed rice; interpret with crop stage/management.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','soil_condition','Soil Condition','soil_condition_kala_jeera_v1','kala_jeera_v1','condition',700,'{"soil_ph_suitability":0.20,"soil_soc_suitability":0.20,"soil_cec_suitability":0.10,"soil_bulk_density_suitability":0.10,"soil_texture_suitability":0.25,"drainage_suitability":0.15}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Modeled soil/terrain suitability context; not a laboratory soil test.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','nutrient_stress_risk','Nutrient Stress Risk','nutrient_stress_kala_jeera_v1','kala_jeera_v1','risk',800,'{"optical_nutrient_stress":0.45,"soil_nutrient_stress":0.35,"growth_nutrient_stress":0.20}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Possible nutrient-related stress evidence; does not diagnose N/P/K deficiency.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','erosion_risk','Land / Erosion Risk','erosion_kala_jeera_v1','kala_jeera_v1','risk',850,'{"terrain_erosion_risk":0.25,"bare_exposure":0.20,"rain_erosivity_proxy":0.30,"soil_erodibility_proxy":0.25}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Relative erosion susceptibility proxy; not full RUSLE soil-loss estimation.','{"validation_status":"engineering_default"}','published',true,now()),
('kala_jeera','crop_condition','Overall Crop Condition','crop_condition_kala_jeera_v1','kala_jeera_v1','condition',900,'{"prediction:growth_condition":0.30,"prediction:moisture_condition":0.25,"prediction_inverse:heat_stress":0.10,"prediction_inverse:nutrient_stress_risk":0.15,"prediction_inverse:waterlogging_risk":0.10,"prediction:soil_condition":0.10}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Quality-aware overall crop condition built from preceding deterministic outputs.','{"validation_status":"engineering_default"}','published',true,now()),

-- Mango
('mango','water_stress','Water Stress Risk','water_stress_mango_v1','mango_v1','risk',100,'{"canopy_moisture_stress":0.20,"rootzone_moisture_stress":0.18,"rainfall_stress":0.12,"thermal_stress":0.18,"et_deficit_stress":0.10,"atmospheric_demand_stress":0.12,"sar_anomaly":0.10}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{"rain_window_days":30}','Multi-source mango water-stress evidence score.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','moisture_condition','Crop Moisture Condition','moisture_condition_mango_v1','mango_v1','condition',200,'{"canopy_moisture_condition":0.45,"rootzone_moisture_condition":0.35,"sar_condition":0.20}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Current canopy/root-zone moisture condition.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','growth_condition','Canopy Growth Condition','growth_condition_mango_v1','mango_v1','condition',300,'{"vegetation_condition":0.30,"growth_trend_condition":0.25,"growth_trajectory_condition":0.25,"moisture_support_condition":0.10,"climate_support_condition":0.10}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Canopy/vegetative growth condition; not fruit-load prediction.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','growth_anomaly','Growth Anomaly','growth_anomaly_mango_v1','mango_v1','risk',400,'{"temporal_anomaly":0.35,"spatial_anomaly":0.20,"environmental_stress_evidence":0.20,"growth_trajectory_anomaly":0.25}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Temporal, spatial and trajectory anomaly score.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','heat_stress','Heat Stress Risk','heat_stress_mango_v1','mango_v1','risk',500,'{"lst_stress":0.45,"air_temperature_stress":0.20,"atmospheric_demand_stress":0.25,"et0_stress":0.10}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Thermal and atmospheric-demand risk.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','waterlogging_risk','Waterlogging / Excess Water Risk','waterlogging_mango_v1','mango_v1','risk',600,'{"optical_water_signal":0.15,"wet_soil_signal":0.15,"rain_excess":0.20,"ponding_terrain":0.25,"historic_water_context":0.15,"sar_anomaly":0.10}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{"rain_window_days":14}','Excess-water and drainage risk evidence.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','soil_condition','Soil Condition','soil_condition_mango_v1','mango_v1','condition',700,'{"soil_ph_suitability":0.20,"soil_soc_suitability":0.20,"soil_cec_suitability":0.15,"soil_bulk_density_suitability":0.10,"soil_texture_suitability":0.20,"drainage_suitability":0.15}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Modeled soil/terrain suitability context; not a laboratory soil test.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','nutrient_stress_risk','Nutrient Stress Risk','nutrient_stress_mango_v1','mango_v1','risk',800,'{"optical_nutrient_stress":0.40,"soil_nutrient_stress":0.40,"growth_nutrient_stress":0.20}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Possible nutrient-related stress evidence; does not diagnose N/P/K deficiency.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','erosion_risk','Land / Erosion Risk','erosion_mango_v1','mango_v1','risk',850,'{"terrain_erosion_risk":0.35,"bare_exposure":0.25,"rain_erosivity_proxy":0.15,"soil_erodibility_proxy":0.25}','{"normal":20,"watch":40,"attention":60,"high":80,"affected_threshold":60}','{}','Relative erosion susceptibility proxy; not full RUSLE soil-loss estimation.','{"validation_status":"engineering_default"}','published',true,now()),
('mango','crop_condition','Overall Crop Condition','crop_condition_mango_v1','mango_v1','condition',900,'{"prediction:growth_condition":0.25,"prediction:moisture_condition":0.20,"prediction_inverse:heat_stress":0.15,"prediction_inverse:nutrient_stress_risk":0.20,"prediction_inverse:waterlogging_risk":0.10,"prediction:soil_condition":0.10}','{"critical":20,"poor":40,"attention":60,"fair":80,"affected_threshold":40}','{}','Quality-aware overall crop condition built from preceding deterministic outputs.','{"validation_status":"engineering_default"}','published',true,now())
ON CONFLICT (crop_code, prediction_key, formula_version) DO NOTHING;

COMMIT;
