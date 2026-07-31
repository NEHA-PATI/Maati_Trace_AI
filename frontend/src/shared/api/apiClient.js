import { environment } from "@/app/config/environment";
import { getDeviceId } from "@/features/auth/device";
import {
  clearSession,
  getAccessToken,
  isAccessTokenFresh,
  setSession,
} from "@/features/auth/session";
import { logger } from "@/shared/logging/logger";
import { ApiError } from "@/shared/api/ApiError";
import { serviceBaseUrl, servicePath } from "@/shared/api/serviceUrls";

let refreshPromise = null;

function joinUrl(base, path) {
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function getCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;
  const item = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith(prefix));
  return item ? decodeURIComponent(item.slice(prefix.length)) : null;
}

function safePathForLog(path) {
  const queryIndex = String(path).indexOf("?");
  return queryIndex >= 0 ? `${String(path).slice(0, queryIndex)}?[REDACTED]` : String(path);
}

function correlationId() {
  return globalThis.crypto?.randomUUID?.() || `web-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function readPayload(response) {
  const contentType = response.headers.get("content-type") || "";
  if (response.status === 204) return null;
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
  return response.text();
}

function toApiError(response, payload, fallbackCorrelationId) {
  const detail = payload?.detail && typeof payload.detail === "object" ? payload.detail : {};
  const message = detail.message || payload?.message || response.statusText || "The request failed.";
  return new ApiError(message, {
    status: response.status,
    code: detail.code || "REQUEST_FAILED",
    correlationId: detail.correlation_id || response.headers.get("x-correlation-id") || fallbackCorrelationId,
    fields: detail.fields || [],
    payload,
  });
}

function isNativeRequestBody(body) {
  return typeof body === "string"
    || body instanceof FormData
    || body instanceof URLSearchParams
    || body instanceof Blob
    || body instanceof ArrayBuffer;
}

function serialiseBody(body) {
  if (body === undefined || body === null) return body;
  return isNativeRequestBody(body) ? body : JSON.stringify(body);
}

function buildHeaders({ headers, authMode, csrf, requestCorrelationId, body }) {
  const result = new Headers(headers || {});
  result.set("Accept", "application/json");
  result.set("X-Device-ID", getDeviceId());
  result.set("X-Correlation-ID", requestCorrelationId);

  if (body !== undefined && body !== null && !(body instanceof FormData) && !result.has("Content-Type")) {
    result.set("Content-Type", "application/json");
  }

  if (authMode !== "public") {
    const token = getAccessToken();
    if (token) result.set("Authorization", `Bearer ${token}`);
  }

  if (csrf) {
    const csrfToken = getCookie(environment.csrfCookieName);
    if (csrfToken) result.set("X-CSRF-Token", csrfToken);
  }

  return result;
}

async function execute(path, options = {}) {
  const {
    method = "GET",
    body,
    headers,
    authMode = "public",
    csrf = false,
    timeoutMs = environment.requestTimeoutMs,
    signal,
    retryOnAuth = authMode === "required",
    _retried = false,
    serviceName = "auth",
  } = options;

  if (authMode === "required" && !_retried && !isAccessTokenFresh()) {
    await refreshAccessSession();
  }

  const requestCorrelationId = correlationId();
  const requestHeaders = buildHeaders({ headers, authMode, csrf, requestCorrelationId, body });
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const startedAt = performance.now();
  const url = joinUrl(serviceBaseUrl(serviceName), servicePath(path));

  const loggedPath = safePathForLog(path);
  logger.debug("api_request_started", { serviceName, method, path: loggedPath, authMode, correlationId: requestCorrelationId });

  try {
    const response = await fetch(url, {
      method,
      credentials: "include",
      headers: requestHeaders,
      body: serialiseBody(body),
      signal: signal || controller.signal,
    });

    const payload = await readPayload(response);
    const responseCorrelationId = response.headers.get("x-correlation-id") || requestCorrelationId;

    logger.info("api_request_completed", {
      serviceName,
      method,
      path: loggedPath,
      status: response.status,
      durationMs: Math.round(performance.now() - startedAt),
      correlationId: responseCorrelationId,
    });

    if (response.status === 401 && retryOnAuth && !_retried) {
      try {
        await refreshAccessSession();
      } catch (refreshError) {
        clearSession();
        throw refreshError;
      }
      return execute(path, { ...options, _retried: true, retryOnAuth: false });
    }

    if (!response.ok) throw toApiError(response, payload, responseCorrelationId);
    return payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    const message = error?.name === "AbortError" ? "The request timed out." : error?.message || "The request failed.";
    logger.error("api_request_failed", {
      serviceName,
      method,
      path: loggedPath,
      message,
      durationMs: Math.round(performance.now() - startedAt),
      correlationId: requestCorrelationId,
    });
    throw new ApiError(message, {
      status: 0,
      code: error?.name === "AbortError" ? "REQUEST_TIMEOUT" : "NETWORK_ERROR",
      correlationId: requestCorrelationId,
    });
  } finally {
    window.clearTimeout(timer);
  }
}

async function performRefresh() {
  const requestCorrelationId = correlationId();
  const headers = buildHeaders({
    headers: {},
    authMode: "public",
    csrf: true,
    requestCorrelationId,
    body: null,
  });
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), environment.requestTimeoutMs);

  try {
    const response = await fetch(joinUrl(serviceBaseUrl("auth"), servicePath("/v1/auth/refresh")), {
      method: "POST",
      credentials: "include",
      headers,
      signal: controller.signal,
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      clearSession();
      throw toApiError(response, payload, response.headers.get("x-correlation-id") || requestCorrelationId);
    }
    setSession(payload);
    logger.info("auth_refresh_succeeded", {
      status: response.status,
      correlationId: response.headers.get("x-correlation-id") || requestCorrelationId,
    });
    return payload;
  } catch (error) {
    clearSession();
    logger.warn("auth_refresh_failed", {
      code: error?.code,
      status: error?.status,
      correlationId: error?.correlationId || requestCorrelationId,
    });
    if (error instanceof ApiError) throw error;
    throw new ApiError(error?.message || "Session refresh failed.", {
      code: "REFRESH_FAILED",
      correlationId: requestCorrelationId,
    });
  } finally {
    window.clearTimeout(timer);
  }
}

export function refreshAccessSession() {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export const apiClient = Object.freeze({ request: execute });
