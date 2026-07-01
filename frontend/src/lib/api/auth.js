import { apiRequest } from "./client";

export const signup = (payload) => apiRequest("/api/auth/signup", { method: "POST", body: JSON.stringify(payload) });
export const login = (payload) => apiRequest("/api/auth/login", { method: "POST", body: JSON.stringify(payload) });
export const getMe = () => apiRequest("/api/auth/me");
export const refresh = (refreshToken) => apiRequest("/api/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) });
export const logout = (refreshToken) => apiRequest("/api/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) });
