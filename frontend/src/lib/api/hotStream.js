import { apiRequest } from "./client";

export const repairFarm = (farmId) =>
  apiRequest(`/api/hot-stream/farms/${farmId}/repair`, { method: "POST" });

export const materializeFarmAnalysis = (farmId, payload) =>
  apiRequest(`/api/farm-analysis/${farmId}/materialize`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const materializeFarmTrends = (farmId, payload) =>
  apiRequest(`/api/hot-stream/farms/${farmId}/trends/materialize`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const materializeFarmGrid = (farmId, payload) =>
  apiRequest(`/api/hot-stream/farms/${farmId}/grid/materialize`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
