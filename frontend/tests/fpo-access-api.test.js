import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/shared/api/apiClient";
import { fpoAccessApi } from "@/features/fpo-access/api/fpoAccessApi";

vi.mock("@/shared/api/apiClient", () => ({
  apiClient: { request: vi.fn() },
}));

describe("FPO access admin requests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads pending, approved, and expired invitations without duplicate requests", async () => {
    apiClient.request
      .mockResolvedValueOnce({
        items: [{ request_id: "pending", created_at: "2026-11-02T10:00:00Z" }],
      })
      .mockResolvedValueOnce({
        items: [{ request_id: "approved", created_at: "2026-11-02T11:00:00Z" }],
      })
      .mockResolvedValueOnce({
        items: [
          { request_id: "expired", created_at: "2026-11-02T09:00:00Z" },
          { request_id: "approved", created_at: "2026-11-02T11:00:00Z" },
        ],
      });

    const result = await fpoAccessApi.listActionableForAdmin();

    expect(apiClient.request).toHaveBeenNthCalledWith(
      1,
      "/v1/auth/admin/fpo-access-requests?status=pending&limit=50&offset=0",
      { authMode: "required" },
    );
    expect(apiClient.request).toHaveBeenNthCalledWith(
      3,
      "/v1/auth/admin/fpo-access-requests?status=expired_invitation&limit=50&offset=0",
      { authMode: "required" },
    );
    expect(result.items.map((item) => item.request_id)).toEqual([
      "approved",
      "pending",
      "expired",
    ]);
  });
});
