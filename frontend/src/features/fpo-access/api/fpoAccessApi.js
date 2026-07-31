import { apiClient } from "@/shared/api/apiClient";

export const fpoAccessApi = Object.freeze({
  submit: (payload) => apiClient.request("/v1/auth/fpo-access-requests", {
    method: "POST",
    body: payload,
  }),
  listForAdmin: ({ status = "pending", limit = 50, offset = 0 } = {}) => apiClient.request(
    `/v1/auth/admin/fpo-access-requests?status=${encodeURIComponent(status)}&limit=${limit}&offset=${offset}`,
    { authMode: "required" },
  ),
  reviewForAdmin: (requestId, payload) => apiClient.request(`/v1/auth/admin/fpo-access-requests/${requestId}`, {
    method: "PATCH",
    authMode: "required",
    body: payload,
  }),
  createInvitation: (payload) => apiClient.request("/v1/auth/admin/invitations", {
    method: "POST",
    authMode: "required",
    body: payload,
  }),
});
