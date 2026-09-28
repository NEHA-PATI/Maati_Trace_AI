import { fpoManagementClient } from "@/shared/api/serviceClients";

export function getFpoAlerts(status = "OPEN") {
  return fpoManagementClient.request(`/v1/fpo-portal/alerts?status=${encodeURIComponent(status)}`);
}
