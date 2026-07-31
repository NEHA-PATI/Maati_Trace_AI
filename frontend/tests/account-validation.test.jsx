import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import AccountStep from "@/features/auth/signup/AccountStep";

describe("signup account validation", () => {
  it("shows field-level errors and rejects an invalid Indian phone", async () => {
    const user = userEvent.setup();
    const onContinue = vi.fn();
    render(<MemoryRouter><AccountStep onContinue={onContinue} loading={false} /></MemoryRouter>);
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByText("Enter your full name.")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Full name"), "Neha Pati");
    await user.type(screen.getByLabelText("Email address"), "neha@example.com");
    await user.type(screen.getByLabelText("Indian mobile number"), "12345");
    await user.type(screen.getByLabelText("Create password"), "correct horse battery staple");
    await user.type(screen.getByLabelText("Confirm password"), "correct horse battery staple");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByText("Enter a valid 10-digit Indian mobile number.")).toBeInTheDocument();
    expect(onContinue).not.toHaveBeenCalled();
  });
});
