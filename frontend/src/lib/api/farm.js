import { boundaryIndexClient, farmRegistryClient } from "./client";

export function getFarm(farmId) {
  return farmRegistryClient.request(`/v1/farms/${farmId}`);
}

export function getFarms(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return farmRegistryClient.request(`/v1/farms${query ? `?${query}` : ""}`);
}

export function registerFarm(payload) {
  return farmRegistryClient.request("/v1/farms/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getFarmsByFarmer(farmerId) {
  return farmRegistryClient.request(`/v1/farmers/${farmerId}/farms`);
}

export function previewH3(payload) {
  return boundaryIndexClient.request("/v1/h3/preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
