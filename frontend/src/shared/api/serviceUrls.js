import { environment } from "@/app/config/environment";

function trimTrailingSlash(value) {
  return String(value || "").replace(
    /\/+$/,
    "",
  );
}

export function serviceBaseUrl() {
  if (!environment.apiGatewayUrl) {
    throw new Error(
      "VITE_API_GATEWAY_URL is required.",
    );
  }

  return trimTrailingSlash(
    environment.apiGatewayUrl,
  );
}

export function servicePath(path) {
  const normalizedPath = String(
    path || "",
  ).startsWith("/")
    ? String(path)
    : `/${path}`;

  if (
    normalizedPath.startsWith("/api/")
  ) {
    return normalizedPath;
  }

  if (
    normalizedPath.startsWith("/v1/")
  ) {
    return `/api/${normalizedPath.slice(4)}`;
  }

  return normalizedPath;
}
