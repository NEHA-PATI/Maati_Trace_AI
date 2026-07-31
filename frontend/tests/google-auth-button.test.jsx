import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/app/config/environment", () => ({ environment: { googleClientId: "test-client" } }));
import GoogleAuthButton from "@/features/auth/components/GoogleAuthButton";

describe("GoogleAuthButton", () => {
  beforeEach(() => {
    window.google = {
      accounts: {
        id: {
          initialize: vi.fn(({ callback }) => { window.__googleCallback = callback; }),
          renderButton: vi.fn(),
        },
      },
    };
  });

  it("returns the credential to its owner exactly once", async () => {
    const onSuccess = vi.fn();
    render(<GoogleAuthButton onSuccess={onSuccess} onError={vi.fn()} />);
    await waitFor(() => expect(window.google.accounts.id.initialize).toHaveBeenCalledOnce());
    window.__googleCallback({ credential: "google-id-token" });
    await waitFor(() => expect(onSuccess).toHaveBeenCalledOnce());
    expect(onSuccess).toHaveBeenCalledWith("google-id-token");
  });
});
