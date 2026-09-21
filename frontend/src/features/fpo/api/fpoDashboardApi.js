import { fpoManagementClient } from "@/shared/api/serviceClients";

export function getFpoDashboardReport() {
  return fpoManagementClient.request("/v1/fpo-portal/dashboard");
}

export function getFpoDashboardAlerts(status = "OPEN") {
  return fpoManagementClient.request(`/v1/fpo-portal/alerts?status=${encodeURIComponent(status)}`);
}

export function acknowledgeFpoDashboardAlert(alertId) {
  return fpoManagementClient.request(`/v1/fpo-portal/alerts/${alertId}/acknowledge`, { method: "PATCH", body: {} });
}
