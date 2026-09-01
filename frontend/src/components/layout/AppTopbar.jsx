import {
  useState,
} from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { Bell } from "lucide-react";

import { useAuth } from "@/features/auth/context/useAuth";

const NAV_ITEMS = [
  { to: "/farmer/me", label: "Dashboard" },
  { to: "/my-crops", label: "My Crop" },
  { to: "/", label: "Home" },
  { to: "/our-method", label: "Our Method" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/plans", label: "Plans" },
  { to: "/settings", label: "Profile" },
  { to: "/farm-register", label: "Register" },
];

function MaatiLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#f4f0df] shadow-sm ring-1 ring-black/10">
        <img
          src="/MaatiAI.png"
          alt="MaatiTrace logo"
          className="h-8 w-8 object-contain"
        />
      </div>
      <div className="leading-tight">
        <div className="text-sm font-black tracking-[0.24em]">
          MAATITRACE
        </div>
        <div className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
          Field Intelligence Platform
        </div>
      </div>
    </div>
  );
}

export default function AppTopbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [loggingOut, setLoggingOut] =
    useState(false);
  const [logoutError, setLogoutError] =
    useState("");

  async function handleLogout() {
    setLoggingOut(true);
    setLogoutError("");

    try {
      await logout();
      navigate("/login", {
        replace: true,
      });
    } catch (error) {
      setLogoutError(
        error?.message
          || "Logout failed.",
      );
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-border bg-background/90 backdrop-blur-md">
      <div className="mx-auto grid max-w-[1600px] grid-cols-[1fr_auto] items-center gap-3 px-4 py-3 md:h-16 md:grid-cols-[1fr_auto_1fr] md:py-0">
        <Link
          to="/"
          aria-label="MaatiTrace home"
          className="justify-self-start"
        >
          <MaatiLogo />
        </Link>

        <nav className="order-3 col-span-2 flex items-center gap-2 overflow-x-auto pb-1 md:order-none md:col-span-1 md:justify-center md:overflow-visible md:pb-0">
          {NAV_ITEMS.map((item) => {
            const active =
              location.pathname === item.to;

            return (
              <Link
                key={item.to}
                to={item.to}
                className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] transition-colors ${
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground/75 hover:bg-secondary hover:text-foreground"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center justify-self-end gap-2">
          <Link
            to="/notifications"
            aria-label="Notifications"
            title="Notifications"
            className={`grid h-10 w-10 shrink-0 place-items-center rounded-full border transition-colors ${
              location.pathname === "/notifications"
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-foreground/75 hover:bg-secondary hover:text-foreground"
            }`}
          >
            <Bell className="h-4 w-4" aria-hidden="true" />
          </Link>
          <span className="flex flex-col items-end gap-1">
            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              className="rounded-full border border-border px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-foreground/75 transition-colors hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loggingOut
                ? "Logging out..."
                : "Log out"}
            </button>
            {logoutError ? (
              <span
                role="alert"
                className="max-w-48 text-right text-[10px] font-semibold text-rose-600"
              >
                {logoutError}
              </span>
            ) : null}
          </span>
        </div>
      </div>
    </header>
  );
}
