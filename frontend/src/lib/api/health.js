import { gatewayClient } from "@/shared/api/serviceClients";

const HEALTH_ROUTE = "/api/health";

export const getServiceHealth = () => ({
  auth: gatewayClient.request(`${HEALTH_ROUTE}/auth/live`),
  location: gatewayClient.request(`${HEALTH_ROUTE}/location/live`),
  registry: gatewayClient.request(`${HEALTH_ROUTE}/registry/live`),
  boundary: gatewayClient.request(`${HEALTH_ROUTE}/boundary/live`),
  stac: gatewayClient.request(`${HEALTH_ROUTE}/stac/live`),
  raster: gatewayClient.request(`${HEALTH_ROUTE}/raster/live`),
  lakehouse: gatewayClient.request(`${HEALTH_ROUTE}/lakehouse/live`),
  orchestrator: gatewayClient.request(`${HEALTH_ROUTE}/orchestrator/live`),
  analytics: gatewayClient.request(`${HEALTH_ROUTE}/analytics/live`),
});

export async function getAllServiceHealth() {
  const entries = Object.entries(getServiceHealth());
  const resolved = await Promise.all(entries.map(async ([name, promise]) => [name, await promise.catch((error) => ({ status: "unhealthy", error: error?.message || "Request failed" }))]));
  return Object.fromEntries(resolved);
}
