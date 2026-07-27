import { authClient } from "./client";

export function startSignup(payload) {
  return authClient.request("/v1/auth/signup/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function verifySignupOtp(payload) {
  return authClient.request("/v1/auth/signup/verify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function completeSignup(payload) {
  return authClient.request("/v1/auth/signup/complete", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(payload) {
  return authClient.request("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginWithGoogle(idToken) {
  return authClient.request("/v1/auth/google", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken }),
  });
}

export function refresh(refreshToken) {
  return authClient.request("/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function logout(refreshToken) {
  return authClient.request("/v1/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function getMe() {
  return authClient.request("/v1/auth/me", {
    method: "GET",
  });
}