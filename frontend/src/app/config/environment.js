export const environment = Object.freeze({
  apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000",
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
  csrfCookieName: import.meta.env.VITE_CSRF_COOKIE_NAME || "maatitrace_csrf",
  requestTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS || 300000),
  otpMaxResends: Number(import.meta.env.VITE_SIGNUP_OTP_MAX_RESENDS || 3),
  logLevel: import.meta.env.VITE_LOG_LEVEL || (import.meta.env.DEV ? "debug" : "warn"),
});

export function assertFrontendEnvironment() {
  const errors = [];
  if (!environment.apiGatewayUrl) errors.push("VITE_API_GATEWAY_URL is required");
  if (!Number.isFinite(environment.requestTimeoutMs) || environment.requestTimeoutMs < 1000) errors.push("VITE_API_TIMEOUT_MS must be at least 1000");
  if (errors.length) throw new Error(`Frontend configuration is invalid:\n- ${errors.join("\n- ")}`);
}
