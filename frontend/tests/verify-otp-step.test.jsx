import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import VerifyOtpStep from "@/features/auth/signup/VerifyOtpStep";

describe("VerifyOtpStep countdown and resend", () => {
  beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
  afterEach(() => vi.useRealTimers());

  it("enables resend after cooldown and reports remaining sends", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const onResend = vi.fn();
    render(
      <VerifyOtpStep
        maskedEmail="ne****@example.com"
        otp=""
        onOtpChange={vi.fn()}
        onVerify={vi.fn()}
        onResend={onResend}
        onBack={vi.fn()}
        loading={false}
        error=""
        expiresAt={Date.now() + 600000}
        resendAvailableAt={Date.now() + 2000}
        resendsRemaining={2}
      />,
    );
    expect(screen.getByRole("button", { name: "Resend in 2s" })).toBeDisabled();
    await act(async () => { vi.advanceTimersByTime(2100); });
    const resend = screen.getByRole("button", { name: "Resend code (2 left)" });
    await user.click(resend);
    expect(onResend).toHaveBeenCalledOnce();
  });
});
