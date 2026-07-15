import { hotStreamClient } from "./client";

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
