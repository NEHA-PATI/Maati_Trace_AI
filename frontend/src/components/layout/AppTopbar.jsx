import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Bell, LogOut } from "lucide-react";

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
    <div className="flex items-center gap-2.5">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f4f0df] shadow-sm ring-1 ring-black/10">
        <img src="/MaatiAI.png" alt="MaatiTrace logo" className="h-7 w-7 object-contain" />
      </span>
      <div className="leading-tight">
        <div className="text-[17px] font-extrabold text-[var(--mt-ink)]">MaatiTrace</div>
        <div className="text-[10.5px] font-semibold text-[var(--mt-ink-faint)]">Land Intelligence</div>
      </div>
    </div>
  );
}

export default function AppTopbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");

  async function handleLogout() {
    setLoggingOut(true);
    setLogoutError("");
    try {
      await logout();
      navigate("/login", { replace: true });
    } catch (error) {
      setLogoutError(error?.message || "Logout failed.");
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <header className="mt-surface fixed inset-x-0 top-0 z-50 border-b border-[var(--mt-line)] bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between gap-3 px-4">
        <Link to="/" aria-label="MaatiTrace home">
          <MaatiLogo />
        </Link>

        <nav className="hidden items-center gap-1.5 md:flex">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`rounded-full px-3.5 py-2 text-[13px] font-bold transition-colors ${
                  active
                    ? "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]"
                    : "text-[var(--mt-ink-soft)] hover:bg-[var(--mt-paper-warm)]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/notifications"
            aria-label="Notifications"
            title="Notifications"
            className={`relative grid h-11 w-11 shrink-0 place-items-center rounded-full border transition-colors ${
              location.pathname === "/notifications"
                ? "border-[var(--mt-leaf)] bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]"
                : "border-[var(--mt-line)] bg-white text-[var(--mt-ink-soft)] hover:bg-[var(--mt-paper-warm)]"
            }`}
          >
            <Bell className="h-[18px] w-[18px]" aria-hidden="true" />
            <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full border-2 border-white bg-[var(--mt-clay)]" />
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="flex h-11 items-center gap-1.5 rounded-full border border-[var(--mt-line)] bg-white px-3.5 text-[13px] font-bold text-[var(--mt-ink-soft)] transition-colors hover:bg-[var(--mt-paper-warm)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">{loggingOut ? "Logging out…" : "Log out"}</span>
          </button>
        </div>
      </div>
      {logoutError ? (
        <p role="alert" className="px-4 pb-2 text-right text-[11px] font-semibold text-[var(--mt-clay-text)]">
          {logoutError}
        </p>
      ) : null}
    </header>
  );
}
