import { hotStreamClient } from "@/shared/api/serviceClients";

export const ENVIRONMENT_DATASETS = [["sentinel_2_l2a", "Sentinel-2 optical imagery"], ["sentinel_1_rtc", "Sentinel-1 radar imagery"], ["landsat_c2_l2", "Landsat imagery"], ["gpm_imerg", "GPM rainfall"], ["cop_dem_glo30", "Elevation model"], ["esa_worldcover", "Land-cover map"], ["jrc_surface_water", "Surface-water history"], ["era5_land", "ERA5-Land weather"], ["soilgrids_v2", "SoilGrids soil data"], ["smap_l4_sm", "SMAP soil moisture"], ["modis_et", "MODIS evapotranspiration"], ["modis_lai_fpar", "MODIS vegetation"], ["weather_forecast", "Weather forecast"]];

export const ANALYSIS_PIPELINE_STEPS = [["farm_ready", "Prepare farm metadata"], ...ENVIRONMENT_DATASETS.map(([key, label]) => [`environment:${key}`, label]), ["trends", "Compute farm trends"], ["grid_context", "Prepare display grid"], ["intelligence", "Build crop intelligence"]];

export const repairFarm = (farmId) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/repair`, { method: "POST" });

export const materializeFarmAnalysis = (farmId, payload) =>
  hotStreamClient.request(`/v1/farm-analysis/${farmId}/materialize`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const materializeFarmTrends = (farmId) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/trends/materialize`, {
    method: "POST",
  });

export const materializeFarmGrid = (farmId) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/grid/materialize`, {
    method: "POST",
  });

export const fullRefreshFarm = (farmId, payload) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/full-refresh`, {
    method: "POST",
    body: payload ? JSON.stringify(payload) : undefined,
  });

// Canonical farmer workflow. The request is queued and the caller polls the
// status endpoint while the orchestrator runs every source and intelligence
// stage in order.
export const runLatestAnalysis = (farmId, payload = {}) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/run-latest-analysis`, {
    method: "POST",
    body: payload,
  });

export const getLatestAnalysisStatus = (farmId) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/analysis-status`);

export const backfillSentinel2History = (farmId, payload) =>
  hotStreamClient.request(`/v1/hot-stream/farms/${farmId}/sentinel2/history-backfill`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
