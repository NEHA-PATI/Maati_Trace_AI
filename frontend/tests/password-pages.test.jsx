import { http, HttpResponse } from "msw";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import ForgotPasswordPage from "@/features/auth/pages/ForgotPasswordPage";
import ResetPasswordPage from "@/features/auth/pages/ResetPasswordPage";
import { server } from "@/test/mocks/server";

const BASE = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000";

describe("password recovery pages", () => {
  it("submits a real forgot-password request", async () => {
    const user = userEvent.setup();
    let received;
    server.use(http.post(`${BASE}/api/auth/password/forgot`, async ({ request }) => {
      received = await request.json();
      return HttpResponse.json({ message: "If an eligible account exists, a password reset email will be sent shortly.", correlation_id: "c1" });
    }));
    render(<MemoryRouter><ForgotPasswordPage /></MemoryRouter>);
    await user.type(screen.getByLabelText("Email address"), "Neha@Example.com");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByText(/eligible account exists/)).toBeInTheDocument();
    expect(received).toEqual({ email: "neha@example.com" });
  });

  it("submits the URL reset token and new password", async () => {
    const user = userEvent.setup();
    let received;
    server.use(http.post(`${BASE}/api/auth/password/reset`, async ({ request }) => {
      received = await request.json();
      return HttpResponse.json({ message: "Password reset completed.", correlation_id: "c2" });
    }));
    render(<MemoryRouter initialEntries={["/reset-password?token=" + "a".repeat(50)]}><ResetPasswordPage /></MemoryRouter>);
    await user.type(screen.getByLabelText("New password"), "correct horse battery staple");
    await user.type(screen.getByLabelText("Confirm new password"), "correct horse battery staple");
    await user.click(screen.getByRole("button", { name: "Reset password" }));
    expect(await screen.findByText("Password reset completed.")).toBeInTheDocument();
    expect(received.token).toBe("a".repeat(50));
  });
});
