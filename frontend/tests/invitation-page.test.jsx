import { http, HttpResponse } from "msw";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "@/features/auth/context/AuthContext";
import AcceptInvitationPage from "@/features/auth/pages/AcceptInvitationPage";
import { server } from "@/test/mocks/server";

const BASE = import.meta.env.VITE_AUTH_SERVICE_URL || "http://localhost:8002";
const TOKEN = "i".repeat(50);

describe("AcceptInvitationPage", () => {
  it("validates and accepts a real invitation", async () => {
    const user = userEvent.setup();
    const adoptAuthResponse = vi.fn((response) => response.user);
    let accepted;
    server.use(
      http.get(`${BASE}/v1/auth/invitations/validate`, () => HttpResponse.json({ valid: true, masked_email: "fp***@example.com", role: "fpo", expires_at: new Date(Date.now() + 3600000).toISOString() })),
      http.post(`${BASE}/v1/auth/invitations/accept`, async ({ request }) => {
        accepted = await request.json();
        return HttpResponse.json({ access_token: "access", expires_in_seconds: 900, user: { user_id: "1", role: "fpo", full_name: "FPO Leader" } }, { status: 201 });
      }),
    );
    render(
      <AuthContext.Provider value={{ adoptAuthResponse }}>
        <MemoryRouter initialEntries={[`/accept-invitation?token=${TOKEN}`]}>
          <Routes>
            <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
            <Route path="/fpo/me" element={<div>FPO dashboard</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    );
    expect(await screen.findByText(/Account role:/)).toHaveTextContent("fpo");
    await user.type(screen.getByLabelText("Full name"), "FPO Leader");
    await user.type(screen.getByLabelText("Indian mobile number"), "9876543210");
    await user.type(screen.getByLabelText("Create password"), "correct horse battery staple");
    await user.type(screen.getByLabelText("Confirm password"), "correct horse battery staple");
    await user.click(screen.getByRole("button", { name: "Accept invitation" }));
    expect(await screen.findByText("FPO dashboard")).toBeInTheDocument();
    expect(accepted.phone_number).toBe("+919876543210");
    expect(adoptAuthResponse).toHaveBeenCalledOnce();
  });
});
