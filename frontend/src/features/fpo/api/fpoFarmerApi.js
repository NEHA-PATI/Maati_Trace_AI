import { fpoManagementClient } from "@/shared/api/serviceClients";

export function discoverFpoFarmers(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fpoManagementClient.request(`/v1/fpo-portal/farmers${query ? `?${query}` : ""}`);
}
