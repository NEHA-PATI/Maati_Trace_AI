import { authClient } from "./client";

export const signup = (payload) => authClient.request("/v1/auth/signup", { method: "POST", body: JSON.stringify(payload) });
export const startSignup = (payload) => authClient.request("/v1/auth/signup/start", { method: "POST", body: JSON.stringify(payload) });
export const verifySignupOtp = (payload) => authClient.request("/v1/auth/signup/verify-otp", { method: "POST", body: JSON.stringify(payload) });
export const completeSignup = (payload) => authClient.request("/v1/auth/signup/complete", { method: "POST", body: JSON.stringify(payload) });
export const login = (payload) => authClient.request("/v1/auth/login", { method: "POST", body: JSON.stringify(payload) });
export const getMe = () => authClient.request("/v1/auth/me");
export const refresh = (refreshToken) => authClient.request("/v1/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) });
export const logout = (refreshToken) => authClient.request("/v1/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) });
