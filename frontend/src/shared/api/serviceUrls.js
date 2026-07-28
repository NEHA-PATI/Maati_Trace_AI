import { environment } from "@/app/config/environment";

function trimTrailingSlash(value) {
  return String(value || "").replace(/\/+$/, "");
}

export function serviceBaseUrl(serviceName = "auth") {
  const selected = environment.isGatewayMode ? environment.apiGatewayUrl : environment.serviceUrls[serviceName];
  if (!selected) throw new Error(`Missing frontend URL for service: ${serviceName}`);
  return trimTrailingSlash(selected);
}

export function servicePath(path) {
  if (!environment.isGatewayMode) return path.startsWith("/") ? path : `/${path}`;
  if (path.startsWith("/v1/")) return `/api/${path.slice(4)}`;
  return path.startsWith("/") ? path : `/${path}`;
}
