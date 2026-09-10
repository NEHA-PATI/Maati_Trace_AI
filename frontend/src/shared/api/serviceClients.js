import {
  clearSession,
  getSessionSnapshot,
} from "@/features/auth/session";
import { apiClient } from "@/shared/api/apiClient";

export function createServiceClient(serviceName) {
  return Object.freeze({
    serviceName,

    request: (path, options = {}) => {
      const inferredAuthMode =
        path.startsWith("/health")
        || path.startsWith("/api/health/")
        || serviceName === "auth"
        || serviceName === "gateway"
          ? "public"
          : "required";

      return apiClient.request(path, {
        ...options,
        authMode:
          options.authMode || inferredAuthMode,
        serviceName,
      });
    },
  });
}

export const authClient =
  createServiceClient("auth");

export const profileClient =
  createServiceClient("profile");

export const boundaryIndexClient =
  createServiceClient("boundaryIndex");

export const locationClient =
  createServiceClient("location");

export const farmRegistryClient =
  createServiceClient("farmRegistry");

export const stacClient =
  createServiceClient("stac");

export const rasterClient =
  createServiceClient("raster");

export const lakehouseClient =
  createServiceClient("lakehouse");

export const hotStreamClient =
  createServiceClient("hotStream");

export const analyticsClient =
  createServiceClient("analytics");

export const observabilityClient =
  createServiceClient("observability");

export const gatewayClient =
  createServiceClient("gateway");

export const cropObservationClient =
  createServiceClient("cropObservations");

export function getSession() {
  return getSessionSnapshot();
}

export function clearSessionAndRedirect() {
  clearSession();

  window.dispatchEvent(
    new CustomEvent(
      "maatitrace:auth-required",
    ),
  );
}
