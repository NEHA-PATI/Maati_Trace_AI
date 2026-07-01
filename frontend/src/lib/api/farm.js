import { apiRequest } from "./client";

export function getFarm(farmId) {
  return apiRequest(`/api/farms/${farmId}`);
}

export function registerFarm(payload) {
  return apiRequest("/api/farms/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getFarmsByFarmer(farmerId) {
  return apiRequest(`/api/farmers/${farmerId}/farms`);
}

export function previewH3(payload) {
  return apiRequest("/api/h3/preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function uploadFarmSnapshot(farmId, imagePayload) {
  return apiRequest(`/api/farms/${farmId}/snapshot`, {
    method: "POST",
    body: JSON.stringify({ image: imagePayload }),
  });
}
