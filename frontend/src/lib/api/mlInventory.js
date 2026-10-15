import { createServiceClient } from "@/shared/api/serviceClients";

const client = createServiceClient("lakehouseInventory");

export function getInventoryAssets({ state = "", limit = 100 } = {}) {
  const query = new URLSearchParams({ limit: String(limit) });
  if (state) query.set("state", state);
  return client.request(`/v1/lakehouse-inventory/assets?${query.toString()}`);
}

export function reconcileInventory(limit) {
  const query = limit ? `?limit=${encodeURIComponent(limit)}` : "";
  return client.request(`/v1/lakehouse-inventory/reconcile${query}`, { method: "POST" });
}

export function validateInventoryOnce() {
  return client.request("/v1/lakehouse-inventory/validate/once", { method: "POST" });
}

export function getInventoryManifest(limit = 10000) {
  return client.request(`/v1/lakehouse-inventory/manifest?limit=${encodeURIComponent(limit)}`);
}
