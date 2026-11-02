import { createServiceClient } from "@/shared/api/serviceClients";

const client = createServiceClient("scientificStandardization");

export function getScientificRuns({ state = "", limit = 50 } = {}) {
  const query = new URLSearchParams({ limit: String(limit) });
  if (state) query.set("state", state);
  return client.request(`/v1/scientific-standardization/processing/runs?${query.toString()}`);
}

export function getScientificRun(runId) {
  return client.request(`/v1/scientific-standardization/processing/runs/${encodeURIComponent(runId)}`);
}

export function submitScientificRun(payload) {
  return client.request("/v1/scientific-standardization/processing/runs", {
    method: "POST",
    body: payload,
  });
}

export function cancelScientificRun(runId) {
  return client.request(`/v1/scientific-standardization/processing/runs/${encodeURIComponent(runId)}/cancel`, {
    method: "POST",
  });
}

export function retryScientificRun(runId) {
  return client.request(`/v1/scientific-standardization/processing/runs/${encodeURIComponent(runId)}/retry`, {
    method: "POST",
  });
}
