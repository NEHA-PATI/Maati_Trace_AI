import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFpoPortalBootstrap } from "@/features/fpo/api/fpoPortalApi";
import FpoAppShell from "@/features/fpo/shell/FpoAppShell";

vi.mock("@/features/fpo/api/fpoPortalApi", () => ({
  getFpoPortalBootstrap: vi.fn(),
}));

vi.mock("@/features/fpo/shell/FpoSidebar", () => ({ default: () => null }));
vi.mock("@/features/fpo/shell/FpoTopbar", () => ({ default: () => null }));
vi.mock("@/features/fpo/shell/FpoMobileNavigation", () => ({ default: () => null }));

describe("FPO app shell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not fetch portal bootstrap on the provisioning route", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/fpo/provisioning"]}>
          <Routes>
            <Route element={<FpoAppShell />}>
              <Route
                path="/fpo/provisioning"
                element={<p>Provisioning is visible</p>}
              />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Provisioning is visible")).toBeInTheDocument();
    expect(getFpoPortalBootstrap).not.toHaveBeenCalled();
  });
});
