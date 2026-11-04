import { act, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFpoBootstrapStatus } from "@/features/fpo/api/fpoPortalApi";
import FpoProvisioningPage from "@/features/fpo/access/FpoProvisioningPage";

vi.mock("@/features/fpo/api/fpoPortalApi", () => ({
  getFpoBootstrapStatus: vi.fn(),
}));

describe("FPO provisioning page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the stable organization identity after provisioning completes", async () => {
    getFpoBootstrapStatus.mockResolvedValue({
      status: "READY",
      organization: {
        display_name: "Growers Producer Company",
        public_fpo_id: "MTFPO-S21-26-100001-A",
      },
    });

    render(
      <MemoryRouter>
        <FpoProvisioningPage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", {
        name: "Your FPO workspace is ready",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("MTFPO-S21-26-100001-A")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Continue to organization profile" }),
    ).toHaveAttribute("href", "/fpo/profile");
  });

  it("shows a safe support message and correlation reference after a failure", async () => {
    getFpoBootstrapStatus.mockResolvedValue({
      status: "FAILED",
      correlation_id: "8a08a6ef-1fe1-487a-98ad-81515a6034e4",
      error: {
        message: "We could not finish setting up your organization.",
      },
    });

    render(
      <MemoryRouter>
        <FpoProvisioningPage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", {
        name: "We need help finishing setup",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/could not finish setting up/)).toBeInTheDocument();
    expect(screen.getByText("8a08a6ef-1fe1-487a-98ad-81515a6034e4")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Check again" })).toBeInTheDocument();
  });

  it("checks pending provisioning again within five seconds", async () => {
    vi.useFakeTimers();
    getFpoBootstrapStatus
      .mockResolvedValueOnce({
        status: "PENDING",
        next_poll_after_seconds: 2,
      })
      .mockResolvedValueOnce({ status: "READY" });

    try {
      render(
        <MemoryRouter>
          <FpoProvisioningPage />
        </MemoryRouter>,
      );

      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(getFpoBootstrapStatus).toHaveBeenCalledTimes(1);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(5000);
      });
      expect(getFpoBootstrapStatus).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });
});
