import { http, HttpResponse } from "msw";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import FpoAccessRequestPage from "@/features/fpo-access/pages/FpoAccessRequestPage";
import { server } from "@/test/mocks/server";

const BASE = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000";

describe("FPO access request", () => {
  it("submits a review request without creating an account", async () => {
    const user = userEvent.setup();
    let payload;
    server.use(http.post(`${BASE}/api/auth/fpo-access-requests`, async ({ request }) => {
      payload = await request.json();
      return HttpResponse.json({ request_id: "11111111-1111-4111-8111-111111111111", status: "pending", message: "Request received.", correlation_id: "c1" }, { status: 201 });
    }));
    render(<MemoryRouter><FpoAccessRequestPage /></MemoryRouter>);
    await user.type(screen.getByLabelText("FPO organisation name"), "Green Growers FPO");
    await user.type(screen.getByLabelText("Contact person"), "Neha Pati");
    await user.type(screen.getByLabelText("Contact email"), "fpo@example.com");
    await user.type(screen.getByLabelText("Indian mobile number"), "9876543210");
    await user.click(screen.getByRole("button", { name: "Request FPO access" }));
    expect(await screen.findByText("Request received.")).toBeInTheDocument();
    expect(payload.contact_phone).toBe("+919876543210");
    expect(payload).not.toHaveProperty("password");
  });
});
