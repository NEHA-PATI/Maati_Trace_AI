const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
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

export async function apiRequest(path, options = {}) {
  const session = getSession();
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (session?.accessToken) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearSessionAndRedirect();
    throw new ApiError("Session expired. Please log in again.", 401);
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detailMessage =
      payload && typeof payload === "object"
        ? (typeof payload.detail === "string"
            ? payload.detail
            : payload.detail?.message || payload.message)
        : null;
    const message =
      detailMessage ||
      `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, payload);
  }

  return payload;
}

export { API_BASE_URL, getSession, clearSessionAndRedirect };
