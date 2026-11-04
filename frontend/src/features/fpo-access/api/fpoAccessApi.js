import { apiClient } from "@/shared/api/apiClient";

const listForAdmin = ({ status = "pending", limit = 50, offset = 0 } = {}) => apiClient.request(
  `/v1/auth/admin/fpo-access-requests?status=${encodeURIComponent(status)}&limit=${limit}&offset=${offset}`,
  { authMode: "required" },
);

export const fpoAccessApi = Object.freeze({
  submit: (payload) => apiClient.request("/v1/auth/fpo-access-requests", {
    method: "POST",
    body: payload,
  }),
  listForAdmin,
  listActionableForAdmin: async () => {
    const [pending, approved, expired] = await Promise.all([
      listForAdmin({ status: "pending" }),
      listForAdmin({ status: "approved" }),
      listForAdmin({ status: "expired_invitation" }),
    ]);
    const uniqueItems = new Map();
    for (const item of [...pending.items, ...approved.items, ...expired.items]) {
      uniqueItems.set(item.request_id, item);
    }
    return {
      items: [...uniqueItems.values()].sort(
        (left, right) => new Date(right.created_at) - new Date(left.created_at),
      ),
    };
  },
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
