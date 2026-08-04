import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import AppShell from "@/components/layout/AppShell";
import PublicNav from "@/components/layout/PublicNav";
import { AuthContext } from "@/features/auth/context/AuthContext";

const authValue = {
  initialising: false,
  isAuthenticated: true,
  user: { role: "farmer" },
  logout: vi.fn(),
};

function renderWithAuth(element) {
  return render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter>{element}</MemoryRouter>
    </AuthContext.Provider>,
  );
}

function expectAuthenticatedNavigation() {
  expect(screen.getByRole("link", { name: "Profile" })).toHaveAttribute(
    "href",
    "/settings",
  );
  expect(screen.getByRole("link", { name: "Register" })).toHaveAttribute(
    "href",
    "/farm-register",
  );
  expect(screen.getByRole("link", { name: "Notifications" })).toHaveAttribute(
    "href",
    "/notifications",
  );
}

describe("application navigation", () => {
  it("shows profile, registration, and notifications in the protected navbar", () => {
    renderWithAuth(<AppShell>Page content</AppShell>);

    expectAuthenticatedNavigation();
    expect(screen.getByText("Page content")).toBeInTheDocument();
    expect(document.querySelector("aside")).not.toBeInTheDocument();
  });

  it("shows the same destinations in the authenticated public navbar", () => {
    renderWithAuth(<PublicNav />);

    expectAuthenticatedNavigation();
  });
});
