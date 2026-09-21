import { fpoManagementClient } from "@/shared/api/serviceClients";

export function getFpoPortalBootstrap() {
  return fpoManagementClient.request("/v1/fpo-portal/bootstrap");
}

export function getFpoPortalEntitlements() {
  return fpoManagementClient.request("/v1/fpo-portal/entitlements");
}
