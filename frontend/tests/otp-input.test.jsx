import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import OtpInput from "@/features/auth/components/OtpInput";

function Harness() {
  const [value, setValue] = useState("");
  return <><OtpInput value={value} onChange={setValue} /><output>{value}</output></>;
}

describe("OtpInput", () => {
  it("accepts a complete pasted OTP", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByLabelText("OTP digit 1 of 6"));
    await user.paste("12a3456");
    expect(screen.getByText("123456")).toBeInTheDocument();
  });

  it("moves backward on backspace and supports arrow navigation", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const first = screen.getByLabelText("OTP digit 1 of 6");
    await user.click(first);
    await user.keyboard("12");
    const third = screen.getByLabelText("OTP digit 3 of 6");
    expect(third).toHaveFocus();
    await user.keyboard("{ArrowLeft}{Backspace}");
    expect(screen.getByLabelText("OTP digit 1 of 6")).toHaveFocus();
  });
});
