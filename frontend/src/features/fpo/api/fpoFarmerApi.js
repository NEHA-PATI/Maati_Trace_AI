import { fpoManagementClient } from "@/shared/api/serviceClients";

export function discoverFpoFarmers(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fpoManagementClient.request(`/v1/fpo-portal/farmers${query ? `?${query}` : ""}`);
}

export function getFpoFarmMonitoring(query = "") {
  const suffix = query ? `?query=${encodeURIComponent(query)}` : "";
  return fpoManagementClient.request(`/v1/fpo-portal/farms/monitoring${suffix}`);
}

export function getFpoFarmer(farmerId) {
  return fpoManagementClient.request(`/v1/fpo/me/farmers/${encodeURIComponent(farmerId)}`);
}

export function getFpoFarmerFarms(farmerId) {
  return fpoManagementClient.request(`/v1/fpo/me/farmers/${encodeURIComponent(farmerId)}/farms`);
}

export function getFpoFarmIntelligence(farmerId, farmId) {
  return fpoManagementClient.request(`/v1/fpo/me/farmers/${encodeURIComponent(farmerId)}/farms/${encodeURIComponent(farmId)}/intelligence`);
}
