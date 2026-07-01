export function saveSession(authResponse) {
  localStorage.setItem("maatitrace_session", JSON.stringify({
    accessToken: authResponse.access_token,
    refreshToken: authResponse.refresh_token,
    user: authResponse.user,
  }));
}
export function getStoredUser() {
  try { return JSON.parse(localStorage.getItem("maatitrace_session") || "null")?.user || null; } catch { return null; }
}
export function getAccessToken() {
  try { return JSON.parse(localStorage.getItem("maatitrace_session") || "null")?.accessToken || null; } catch { return null; }
}
export function getRefreshToken() {
  try { return JSON.parse(localStorage.getItem("maatitrace_session") || "null")?.refreshToken || null; } catch { return null; }
}
export function clearSession() { localStorage.removeItem("maatitrace_session"); }
export function getDefaultRouteForRole(role) {
  if (role === "admin") return "/admin";
  if (role === "fpo") return "/fpo/me";
  return "/farmer/me";
}
