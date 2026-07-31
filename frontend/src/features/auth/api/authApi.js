import { apiClient, refreshAccessSession } from "@/shared/api/apiClient";

export const authApi = Object.freeze({
  startSignup: (payload) => apiClient.request("/v1/auth/signup/start", { method: "POST", body: payload }),
  resendSignupOtp: (signupSessionId) => apiClient.request("/v1/auth/signup/resend", {
    method: "POST",
    body: { signup_session_id: signupSessionId },
  }),
  verifySignupOtp: (signupSessionId, otp) => apiClient.request("/v1/auth/signup/verify", {
    method: "POST",
    body: { signup_session_id: signupSessionId, otp },
  }),
  cancelSignup: (signupSessionId, reason = "user_changed_details") => apiClient.request("/v1/auth/signup/cancel", {
    method: "POST",
    body: { signup_session_id: signupSessionId, reason },
  }),
  completeSignup: (signupSessionId) => apiClient.request("/v1/auth/signup/complete", {
    method: "POST",
    body: { signup_session_id: signupSessionId },
  }),
  login: (payload) => apiClient.request("/v1/auth/login", { method: "POST", body: payload }),
  googleLogin: (idToken) => apiClient.request("/v1/auth/google", {
    method: "POST",
    body: { id_token: idToken },
  }),
  refresh: () => refreshAccessSession(),
  logout: () => apiClient.request("/v1/auth/logout", { method: "POST", csrf: true }),
  logoutAll: () => apiClient.request("/v1/auth/logout-all", {
    method: "POST",
    authMode: "required",
    csrf: true,
  }),
  getMe: () => apiClient.request("/v1/auth/me", { authMode: "required" }),
  forgotPassword: (email) => apiClient.request("/v1/auth/password/forgot", {
    method: "POST",
    body: { email },
  }),
  resetPassword: (token, newPassword) => apiClient.request("/v1/auth/password/reset", {
    method: "POST",
    body: { token, new_password: newPassword },
  }),
  validateInvitation: (token) => apiClient.request(`/v1/auth/invitations/validate?token=${encodeURIComponent(token)}`),
  acceptInvitation: (payload) => apiClient.request("/v1/auth/invitations/accept", { method: "POST", body: payload }),
});
