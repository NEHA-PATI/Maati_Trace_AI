import { analyticsClient } from "@/shared/api/serviceClients";

function extractItems(response) {
  if (Array.isArray(response)) return response;
  return response?.items || response?.data || response?.grid_cells || response?.grid_values || response?.h3_cells || [];
}

function getFieldValue(response, keys = []) {
  if (!response || Array.isArray(response)) return response;
  for (const key of keys) {
    if (response[key] !== undefined) return response[key];
  }
  return response;
}

export const getFarmSummary = (farmId) => analyticsClient.request(`/v1/analytics/farms/${farmId}/summary`);
export const getLatestSentinel2 = (farmId) => analyticsClient.request(`/v1/analytics/farms/${farmId}/sentinel2/latest`);
export const getSentinel2History = (farmId, limit = 10) => analyticsClient.request(`/v1/analytics/farms/${farmId}/sentinel2/history?limit=${limit}`);
export const getFarmTrends = (farmId) => analyticsClient.request(`/v1/analytics/farms/${farmId}/trends`);
export async function getFarmH3Cells(farmId) {
  const response = await analyticsClient.request(`/v1/analytics/farms/${farmId}/h3-cells`);
  return extractItems(response);
}
export async function getFarmGridCells(farmId) {
  const response = await analyticsClient.request(`/v1/analytics/farms/${farmId}/grid-cells`);
  return extractItems(response);
}
export async function getLatestGridValues(farmId) {
  const response = await analyticsClient.request(`/v1/analytics/farms/${farmId}/grid-values/latest`);
  return extractItems(response);
}
export async function getGridValueHistory(farmId, limit = 10) {
  const response = await analyticsClient.request(`/v1/analytics/farms/${farmId}/grid-values/history?limit=${limit}`);
  return extractItems(response);
}
export async function getFarmerAnalyticsSummary(farmerId) {
  return analyticsClient.request(`/v1/analytics/farmers/${farmerId}/summary`);
}
export async function getFpoAnalyticsSummary(fpoId) {
  return analyticsClient.request(`/v1/analytics/fpos/${fpoId}/summary`);
}

export async function getFarmGridCellDetails(farmId, gridCellId) {
  return analyticsClient.request(`/v1/analytics/farms/${farmId}/grid-cells/${gridCellId}/details`);
}

/* ---------------- Crop feature/formula engine ---------------- */

export async function getCropProfiles() {
  return extractItems(await analyticsClient.request(`/v1/analytics/crop-profiles`));
}
export async function getCalculatedComponents() {
  return extractItems(await analyticsClient.request(`/v1/analytics/components`));
}
export async function getCropFormulas(cropCode = "") {
  const query = cropCode ? `?crop_code=${encodeURIComponent(cropCode)}` : "";
  return extractItems(await analyticsClient.request(`/v1/analytics/formulas${query}`));
}
export async function getLatestGridCalculations(farmId) {
  return extractItems(await analyticsClient.request(`/v1/analytics/farms/${farmId}/grid-calculations/latest`));
}
export async function getLatestFarmCalculations(farmId, scope = "farm") {
  return extractItems(
    await analyticsClient.request(`/v1/analytics/farms/${farmId}/calculations/latest?scope=${encodeURIComponent(scope)}`),
  );
}
export async function getGridCellCalculations(farmId, gridCellId) {
  return extractItems(
    await analyticsClient.request(`/v1/analytics/farms/${farmId}/grid-cells/${gridCellId}/calculations`),
  );
}
export async function materializeFarmFeatures(farmId, payload) {
  return analyticsClient.request(`/v1/analytics/farms/${farmId}/features/materialize`, { method: "POST", body: payload });
}
export async function materializeFarmCalculations(farmId, payload) {
  return analyticsClient.request(`/v1/analytics/farms/${farmId}/calculations/materialize`, { method: "POST", body: payload });
}
export async function materializeFarmIntelligence(farmId, payload) {
  return analyticsClient.request(`/v1/analytics/farms/${farmId}/intelligence/materialize`, { method: "POST", body: payload });
}

