import { hotStreamClient } from "@/shared/api/serviceClients";

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
