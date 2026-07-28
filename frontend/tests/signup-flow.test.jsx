import { http, HttpResponse } from "msw";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "@/features/auth/context/AuthContext";
import SignupFlow from "@/features/auth/signup/SignupFlow";
import { server } from "@/test/mocks/server";

const BASE = import.meta.env.VITE_AUTH_SERVICE_URL || "http://localhost:8002";
const SESSION_1 = "11111111-1111-4111-8111-111111111111";
const SESSION_2 = "22222222-2222-4222-8222-222222222222";

function renderFlow() {
  const adoptAuthResponse = vi.fn((response) => response.user);
  render(
    <MemoryRouter>
      <AuthContext.Provider value={{ adoptAuthResponse }}><SignupFlow /></AuthContext.Provider>
    </MemoryRouter>,
  );
  return { adoptAuthResponse };
}

async function completeAccountForm(user, email = "farmer@example.com") {
  await user.type(screen.getByLabelText("Full name"), "Neha Pati");
  await user.type(screen.getByLabelText("Email address"), email);
  await user.type(screen.getByLabelText("Indian mobile number"), "9876543210");
  await user.type(screen.getByLabelText("Create password"), "correct horse battery staple");
  await user.type(screen.getByLabelText("Confirm password"), "correct horse battery staple");
  await user.click(screen.getByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: "Continue" }));
}

describe("SignupFlow", () => {
  it("has no public role picker and provides the FPO access route", () => {
    renderFlow();
    expect(screen.queryByText("Registering as")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Request access" })).toHaveAttribute("href", "/request-fpo-access");
  });

  it("reuses an unchanged signup session and invalidates it only after identity details change", async () => {
    const user = userEvent.setup();
    let starts = 0;
    let cancels = 0;
    server.use(
      http.post(`${BASE}/v1/auth/signup/start`, async () => {
        starts += 1;
        return HttpResponse.json({
          signup_session_id: starts === 1 ? SESSION_1 : SESSION_2,
          expires_in_seconds: 600,
          resend_available_in_seconds: 60,
          masked_email: "fa****@example.com",
        }, { status: 201 });
      }),
      http.post(`${BASE}/v1/auth/signup/cancel`, () => { cancels += 1; return HttpResponse.json({ cancelled: true }); }),
    );

    renderFlow();
    await completeAccountForm(user);
    await screen.findByText("Check your email");
    expect(starts).toBe(1);

    await user.click(screen.getByRole("button", { name: "â† Change account details" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await screen.findByText("Check your email");
    expect(starts).toBe(1);
    expect(cancels).toBe(0);

    await user.click(screen.getByRole("button", { name: "â† Change account details" }));
    const email = screen.getByLabelText("Email address");
    await user.clear(email);
    await user.type(email, "changed@example.com");
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await waitFor(() => expect(starts).toBe(2));
    expect(cancels).toBe(1);
  });

  it("verifies, completes, signs in, and shows profile/land actions", async () => {
    const user = userEvent.setup();
    server.use(
      http.post(`${BASE}/v1/auth/signup/start`, () => HttpResponse.json({ signup_session_id: SESSION_1, expires_in_seconds: 600, resend_available_in_seconds: 0, masked_email: "fa****@example.com" }, { status: 201 })),
      http.post(`${BASE}/v1/auth/signup/verify`, () => HttpResponse.json({ signup_session_id: SESSION_1, verified: true })),
      http.post(`${BASE}/v1/auth/signup/complete`, () => HttpResponse.json({ access_token: "access", expires_in_seconds: 900, user: { user_id: "1", full_name: "Neha Pati", role: "farmer" } }, { status: 201 })),
    );
    const { adoptAuthResponse } = renderFlow();
    await completeAccountForm(user);
    await user.click(await screen.findByLabelText("OTP digit 1 of 6"));
    await user.paste("123456");
    await user.click(screen.getByRole("button", { name: "Verify and create account" }));
    expect(await screen.findByText("Account created. You are signed in.")).toBeInTheDocument();
    expect(adoptAuthResponse).toHaveBeenCalledOnce();
    expect(screen.getByRole("link", { name: "Complete Profile" })).toHaveAttribute("href", "/settings");
    expect(screen.getByRole("link", { name: "Register Land" })).toHaveAttribute("href", "/farm-register");
  });
});
