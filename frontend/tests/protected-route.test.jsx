import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/components/layout/AppShell", () => ({ default: ({ children }) => <div data-testid="app-shell">{children}</div> }));
import ProtectedRoute from "@/features/auth/components/ProtectedRoute";
import { AuthContext } from "@/features/auth/context/AuthContext";

function renderRoute(authValue, permission = "settings") {
  render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={["/settings"]}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route element={<ProtectedRoute permission={permission} />}>
            <Route path="/settings" element={<div>Settings page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("shows initialisation state", () => {
    renderRoute({ initialising: true, isAuthenticated: false, user: null });
    expect(screen.getByText("Checking your secure session…")).toBeInTheDocument();
  });

  it("redirects unauthenticated users", () => {
    renderRoute({ initialising: false, isAuthenticated: false, user: null });
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders access denied separately from profile completion", () => {
    renderRoute({ initialising: false, isAuthenticated: true, user: { role: "farmer" } }, "adminDashboard");
    expect(screen.getByText("Access denied")).toBeInTheDocument();
  });

  it("renders the protected application shell for an allowed role", () => {
    renderRoute({ initialising: false, isAuthenticated: true, user: { role: "farmer" } });
    expect(screen.getByTestId("app-shell")).toHaveTextContent("Settings page");
  });
});
