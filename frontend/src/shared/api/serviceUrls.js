import { environment } from "@/app/config/environment";

function trimTrailingSlash(value) {
  return String(value || "").replace(/\/+$/, "");
}

export function serviceBaseUrl(serviceName = "auth") {
  return trimTrailingSlash(environment.apiGatewayUrl);
}

export function servicePath(path) {
  if (path.startsWith("/v1/")) return `/api/${path.slice(4)}`;
  return path.startsWith("/") ? path : `/${path}`;
}
