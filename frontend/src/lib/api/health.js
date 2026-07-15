import { authClient, locationClient, farmRegistryClient, stacClient, rasterClient, lakehouseClient, hotStreamClient, analyticsClient, boundaryIndexClient } from "./client";

const HEALTH_PATH = "/health/live";

export const getServiceHealth = () => ({
  auth: authClient.request(HEALTH_PATH),
  location: locationClient.request(HEALTH_PATH),
  registry: farmRegistryClient.request(HEALTH_PATH),
  boundary: boundaryIndexClient.request(HEALTH_PATH),
  stac: stacClient.request(HEALTH_PATH),
  raster: rasterClient.request(HEALTH_PATH),
  lakehouse: lakehouseClient.request(HEALTH_PATH),
  orchestrator: hotStreamClient.request(HEALTH_PATH),
  analytics: analyticsClient.request(HEALTH_PATH),
});

export async function getAllServiceHealth() {
  const entries = Object.entries(getServiceHealth());
  const resolved = await Promise.all(entries.map(async ([name, promise]) => [name, await promise.catch((error) => ({ status: "unhealthy", error: error?.message || "Request failed" }))]));
  return Object.fromEntries(resolved);
}
