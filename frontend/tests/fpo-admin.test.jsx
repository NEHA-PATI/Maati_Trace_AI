import { http, HttpResponse } from "msw";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { clearSession, setSession } from "@/features/auth/session";
import FpoAccessAdminPage from "@/features/fpo-access/pages/FpoAccessAdminPage";
import { server } from "@/test/mocks/server";

const BASE = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000";

describe("FPO access administration", () => {
  beforeEach(() => {
    clearSession();
    setSession({ access_token: "admin-access", expires_in_seconds: 900, user: { user_id: "admin-1", role: "admin" } });
  });

  it("approves a request and queues a secure FPO invitation", async () => {
    const user = userEvent.setup();
    let closed = false;
    let invitationPayload;
    server.use(
      http.get(`${BASE}/api/auth/admin/fpo-access-requests`, ({ request }) => {
        const status = new URL(request.url).searchParams.get("status");
        const item = {
          request_id: "11111111-1111-4111-8111-111111111111",
          organisation_name: "Green Growers FPO",
          registration_number: "FPO-100",
          contact_person_name: "FPO Leader",
          contact_email: "leader@example.com",
          contact_phone: "+919876543210",
          state_name: "Odisha",
          district_name: "Khordha",
          message: "Please verify us.",
          status: "pending",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        const items = !closed && status === "pending" ? [item] : [];
        return HttpResponse.json({ items, total: items.length, limit: 50, offset: 0 });
      }),
      http.patch(`${BASE}/api/auth/admin/fpo-access-requests/:requestId`, async ({ request }) => {
        const body = await request.json();
        if (body.status === "closed") closed = true;
        return HttpResponse.json({
          request_id: "11111111-1111-4111-8111-111111111111",
          organisation_name: "Green Growers FPO",
          contact_person_name: "FPO Leader",
          contact_email: "leader@example.com",
          contact_phone: "+919876543210",
          status: body.status,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }),
      http.post(`${BASE}/api/auth/admin/invitations`, async ({ request }) => {
        invitationPayload = await request.json();
        return HttpResponse.json({
          invitation_id: "22222222-2222-4222-8222-222222222222",
          email: "leader@example.com",
          role: "fpo",
          expires_at: new Date(Date.now() + 3600000).toISOString(),
          message: "Invitation queued.",
        }, { status: 201 });
      }),
    );

    render(<FpoAccessAdminPage />);
    await user.click(await screen.findByRole("button", { name: "Approve and invite" }));
    await waitFor(() => expect(screen.getByText(/Invitation queued/)).toBeInTheDocument());
    expect(invitationPayload).toMatchObject({ email: "leader@example.com", role: "fpo" });
  });
});
