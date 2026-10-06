import { createServiceClient } from "@/shared/api/serviceClients";

const client = createServiceClient("historicalAcquisition");

export function getAcquisitionSources() {
  return client.request("/v1/historical-acquisition/sources");
}

export function previewAcquisition(payload) {
  return client.request("/v1/historical-acquisition/plan", { method: "POST", body: payload });
}

export function submitAcquisition(payload) {
  return client.request("/v1/historical-acquisition/jobs", { method: "POST", body: payload });
}

export function getAcquisitionJobs() {
  return client.request("/v1/historical-acquisition/jobs?limit=100");
}

export function getAcquisitionJob(jobId) {
  return client.request(`/v1/historical-acquisition/jobs/${jobId}`);
}

export function getAcquisitionShards(jobId) {
  return client.request(`/v1/historical-acquisition/jobs/${jobId}/shards?limit=100`);
}

export function retryAcquisitionJob(jobId) {
  return client.request(`/v1/historical-acquisition/jobs/${jobId}/retry`, { method: "POST" });
}

export function cancelAcquisitionJob(jobId) {
  return client.request(`/v1/historical-acquisition/jobs/${jobId}/cancel`, { method: "POST" });
}
