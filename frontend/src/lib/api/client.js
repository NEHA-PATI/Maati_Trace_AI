const API_MODE = import.meta.env.VITE_API_MODE || "direct";
const IS_GATEWAY_MODE = API_MODE === "gateway";
const DEFAULT_TIMEOUT_MS = 180000;

const SERVICE_URLS = {
  auth: import.meta.env.VITE_AUTH_SERVICE_URL,
  boundaryIndex: import.meta.env.VITE_BOUNDARY_INDEX_SERVICE_URL,
  location: import.meta.env.VITE_DISTRICT_BOUNDARY_SERVICE_URL,
  farmRegistry: import.meta.env.VITE_FARM_REGISTRY_SERVICE_URL,
  stac: import.meta.env.VITE_STAC_CATALOG_SERVICE_URL,
  raster: import.meta.env.VITE_RASTER_PROCESSOR_SERVICE_URL,
  lakehouse: import.meta.env.VITE_LAKEHOUSE_WRITER_SERVICE_URL,
  hotStream: import.meta.env.VITE_HOT_STREAM_ORCHESTRATOR_SERVICE_URL,
  analytics: import.meta.env.VITE_ANALYTICS_QUERY_SERVICE_URL,
  gateway: import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000",
};

export class ApiError extends Error {
  constructor(message, status, payload, meta = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
    this.meta = meta;
  }
}

function getSession() {
  try {
    return JSON.parse(localStorage.getItem("maatitrace_session") || "null");
  } catch {
    return null;
  }
}

function clearSessionAndRedirect() {
  localStorage.removeItem("maatitrace_session");
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

function normalizeBaseURL(baseURL) {
  if (!baseURL) return "";
  return String(baseURL).replace(/\/$/, "");
}

function joinURL(baseURL, path) {
  return `${normalizeBaseURL(baseURL)}${path.startsWith("/") ? path : `/${path}`}`;
}

function toGatewayPath(path) {
  if (path.startsWith("/v1/")) return `/api/${path.slice(4)}`;
  if (path === "/v1") return "/api";
  return path;
}

function buildErrorMeta({ serviceName, baseURL, path, method, mode, status, detail }) {
  return {
    serviceName,
    baseURL,
    path,
    method,
    mode,
    status,
    detail,
  };
}

function readDetail(payload, responseStatusText) {
  if (payload && typeof payload === "object") {
    if (typeof payload.detail === "string") return payload.detail;
    if (payload.detail?.message) return payload.detail.message;
    if (payload.message) return payload.message;
  }
  return responseStatusText || null;
}

export function createServiceClient({ serviceName, directBaseURL, gatewayBaseURL }) {
  const resolvedDirectBaseURL = normalizeBaseURL(directBaseURL);
  const resolvedGatewayBaseURL = normalizeBaseURL(gatewayBaseURL || SERVICE_URLS.gateway);

  async function request(path, options = {}) {
    const session = getSession();
    const mode = IS_GATEWAY_MODE ? "gateway" : "direct";
    const baseURL = IS_GATEWAY_MODE ? resolvedGatewayBaseURL : resolvedDirectBaseURL;
    const requestPath = IS_GATEWAY_MODE ? toGatewayPath(path) : path;

    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    if (session?.accessToken) {
      headers.set("Authorization", `Bearer ${session.accessToken}`);
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), options.timeoutMs || DEFAULT_TIMEOUT_MS);

    try {
      const response = await fetch(joinURL(baseURL, requestPath), {
        ...options,
        headers,
        signal: options.signal || controller.signal,
      });

      if (response.status === 401) {
        clearSessionAndRedirect();
        throw new ApiError("Session expired. Please log in again.", 401, null, buildErrorMeta({
          serviceName,
          baseURL,
          path: requestPath,
          method: options.method || "GET",
          mode,
          status: 401,
          detail: "unauthorized",
        }));
      }

      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json") ? await response.json() : await response.text();

      if (!response.ok) {
        const detail = readDetail(payload, response.statusText);
        const error = new ApiError(
          `[MaatiTrace API Error]\nmode: ${mode}\nservice: ${serviceName}\nbaseURL: ${baseURL}\npath: ${requestPath}\nstatus: ${response.status}\ndetail: ${detail || "Request failed"}`,
          response.status,
          payload,
          buildErrorMeta({
            serviceName,
            baseURL,
            path: requestPath,
            method: options.method || "GET",
            mode,
            status: response.status,
            detail,
          }),
        );
        console.error(error.message);
        throw error;
      }

      return payload;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      const message = error?.name === "AbortError" ? "Request timed out" : (error?.message || "Request failed");
      const apiError = new ApiError(
        `[MaatiTrace API Error]\nmode: ${mode}\nservice: ${serviceName}\nbaseURL: ${baseURL}\npath: ${requestPath}\nstatus: 0\ndetail: ${message}`,
        0,
        null,
        buildErrorMeta({
          serviceName,
          baseURL,
          path: requestPath,
          method: options.method || "GET",
          mode,
          status: 0,
          detail: message,
        }),
      );
      console.error(apiError.message);
      throw apiError;
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  return { request, serviceName, directBaseURL: resolvedDirectBaseURL, gatewayBaseURL: resolvedGatewayBaseURL };
}

export const authClient = createServiceClient({
  serviceName: "auth_service",
  directBaseURL: SERVICE_URLS.auth,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const boundaryIndexClient = createServiceClient({
  serviceName: "boundary_index_service",
  directBaseURL: SERVICE_URLS.boundaryIndex,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const locationClient = createServiceClient({
  serviceName: "district_boundary_service",
  directBaseURL: SERVICE_URLS.location,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const farmRegistryClient = createServiceClient({
  serviceName: "farm_registry_service",
  directBaseURL: SERVICE_URLS.farmRegistry,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const stacClient = createServiceClient({
  serviceName: "stac_catalog_service",
  directBaseURL: SERVICE_URLS.stac,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const rasterClient = createServiceClient({
  serviceName: "raster_processor_service",
  directBaseURL: SERVICE_URLS.raster,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const lakehouseClient = createServiceClient({
  serviceName: "lakehouse_writer_service",
  directBaseURL: SERVICE_URLS.lakehouse,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const hotStreamClient = createServiceClient({
  serviceName: "hot_stream_orchestrator_service",
  directBaseURL: SERVICE_URLS.hotStream,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const analyticsClient = createServiceClient({
  serviceName: "analytics_query_service",
  directBaseURL: SERVICE_URLS.analytics,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export const gatewayClient = createServiceClient({
  serviceName: "api_gateway_service",
  directBaseURL: SERVICE_URLS.gateway,
  gatewayBaseURL: SERVICE_URLS.gateway,
});

export { API_MODE, IS_GATEWAY_MODE, SERVICE_URLS, getSession, clearSessionAndRedirect };
