import { apiRequest } from "./client";

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

export const getFarmSummary = (farmId) => apiRequest(`/api/analytics/farms/${farmId}/summary`);
export const getLatestSentinel2 = (farmId) => apiRequest(`/api/analytics/farms/${farmId}/sentinel2/latest`);
export const getSentinel2History = (farmId, limit = 10) => apiRequest(`/api/analytics/farms/${farmId}/sentinel2/history?limit=${limit}`);
export const getFarmTrends = (farmId) => apiRequest(`/api/analytics/farms/${farmId}/trends`);
export async function getFarmH3Cells(farmId) {
  const response = await apiRequest(`/api/analytics/farms/${farmId}/h3-cells`);
  return extractItems(response);
}
export async function getFarmGridCells(farmId) {
  const response = await apiRequest(`/api/analytics/farms/${farmId}/grid-cells`);
  return extractItems(response);
}
export async function getLatestGridValues(farmId) {
  const response = await apiRequest(`/api/analytics/farms/${farmId}/grid-values/latest`);
  return extractItems(response);
}
export async function getGridValueHistory(farmId, limit = 10) {
  const response = await apiRequest(`/api/analytics/farms/${farmId}/grid-values/history?limit=${limit}`);
  return extractItems(response);
}
export async function getFarmerAnalyticsSummary(farmerId) {
  return apiRequest(`/api/analytics/farmers/${farmerId}/summary`);
}
export async function getFpoAnalyticsSummary(fpoId) {
  return apiRequest(`/api/analytics/fpos/${fpoId}/summary`);
}

export async function getFarmGridCellDetails(farmId, gridCellId) {
  return apiRequest(`/api/analytics/farms/${farmId}/grid-cells/${gridCellId}/details`);
}
