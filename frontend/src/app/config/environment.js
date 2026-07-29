const API_MODE = import.meta.env.VITE_API_MODE || "direct";

export const environment = Object.freeze({
  apiMode: API_MODE,
  isGatewayMode: API_MODE === "gateway",
  apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000",
  serviceUrls: Object.freeze({
    auth: import.meta.env.VITE_AUTH_SERVICE_URL || "http://localhost:8001",
    boundaryIndex: import.meta.env.VITE_BOUNDARY_INDEX_SERVICE_URL || "",
    location: import.meta.env.VITE_DISTRICT_BOUNDARY_SERVICE_URL || "",
    farmRegistry: import.meta.env.VITE_FARM_REGISTRY_SERVICE_URL || "",
    stac: import.meta.env.VITE_STAC_CATALOG_SERVICE_URL || "",
    raster: import.meta.env.VITE_RASTER_PROCESSOR_SERVICE_URL || "",
    lakehouse: import.meta.env.VITE_LAKEHOUSE_WRITER_SERVICE_URL || "",
    hotStream: import.meta.env.VITE_HOT_STREAM_ORCHESTRATOR_SERVICE_URL || "",
    analytics: import.meta.env.VITE_ANALYTICS_QUERY_SERVICE_URL || "",
    gateway: import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000",
  }),
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
  csrfCookieName: import.meta.env.VITE_CSRF_COOKIE_NAME || "maatitrace_csrf",
  requestTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS || 30000),
  otpMaxResends: Number(import.meta.env.VITE_SIGNUP_OTP_MAX_RESENDS || 3),
  logLevel: import.meta.env.VITE_LOG_LEVEL || (import.meta.env.DEV ? "debug" : "warn"),
});

export function assertFrontendEnvironment() {
  const errors = [];
  if (!environment.serviceUrls.auth && !environment.isGatewayMode) errors.push("VITE_AUTH_SERVICE_URL is required in direct API mode");
  if (!environment.apiGatewayUrl && environment.isGatewayMode) errors.push("VITE_API_GATEWAY_URL is required in gateway API mode");
  if (!Number.isFinite(environment.requestTimeoutMs) || environment.requestTimeoutMs < 1000) errors.push("VITE_API_TIMEOUT_MS must be at least 1000");
  if (errors.length) throw new Error(`Frontend configuration is invalid:\n- ${errors.join("\n- ")}`);
}
