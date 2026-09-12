import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Bell, LogOut, Menu, X } from "lucide-react";

import { useAuth } from "@/features/auth/context/useAuth";

const NAV_ITEMS = [
  { to: "/", label: "Home" },
  { to: "/our-method", label: "Our Method" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/plans", label: "Plans" },
];

const GET_STARTED_ITEM = {
  to: "/register",
  label: "Get Started",
};

const AUTHENTICATED_NAV_ITEMS = [
  { to: "/farmer/me", label: "Dashboard" },
  { to: "/settings", label: "Profile" },
  { to: "/farm-register", label: "Register" },
];

function MaatiLogo() {
  return (
    <div className="flex items-center gap-2 md:gap-2.5">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#f4f0df] shadow-sm ring-1 ring-black/10 md:h-10 md:w-10">
        <img src="/MaatiAI.png" alt="MaatiTrace logo" className="h-6 w-6 object-contain md:h-7 md:w-7" />
      </span>
      <div className="leading-tight">
        <div className="text-[15px] font-extrabold text-[var(--mt-ink)] md:text-[17px]">MaatiTrace</div>
        <div className="text-[9.5px] font-semibold text-[var(--mt-ink-faint)] md:text-[10.5px]">Land Intelligence</div>
      </div>
    </div>
  );
}

export default function PublicNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, initialising, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = isAuthenticated
    ? [...AUTHENTICATED_NAV_ITEMS, ...NAV_ITEMS]
    : NAV_ITEMS;

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
    <>
      <header className="mt-surface fixed inset-x-0 top-0 z-50 border-b border-[var(--mt-line)] bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between gap-2 px-3 md:h-16 md:gap-3 md:px-4">
        <Link to="/" aria-label="MaatiTrace home">
          <MaatiLogo />
        </Link>

        <nav className="hidden items-center gap-1.5 md:flex">
          {navItems.map((item) => {
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

        <div className="flex shrink-0 items-center gap-1.5 md:gap-2">
          {initialising ? null : isAuthenticated ? (
            <>
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
                className="flex h-10 items-center gap-1.5 rounded-full border border-[var(--mt-line)] bg-white px-3 text-[13px] font-bold text-[var(--mt-ink-soft)] transition-colors hover:bg-[var(--mt-paper-warm)] disabled:cursor-not-allowed disabled:opacity-60 md:h-11 md:px-3.5"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">{loggingOut ? "Logging out…" : "Log out"}</span>
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className={`hidden h-10 items-center rounded-full border px-3 text-[13px] font-bold transition-colors md:flex md:h-11 md:px-3.5 ${
                  location.pathname === "/login"
                    ? "border-[var(--mt-leaf)] bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]"
                    : "border-[var(--mt-line)] bg-white text-[var(--mt-ink-soft)] hover:bg-[var(--mt-paper-warm)]"
                }`}
              >
                Login
              </Link>
              <Link
                to={GET_STARTED_ITEM.to}
                className="hidden h-10 items-center whitespace-nowrap rounded-full bg-[var(--mt-leaf)] px-3 text-[13px] font-bold text-white shadow-sm transition-colors hover:bg-[var(--mt-leaf-deep)] md:flex md:h-11 md:px-4"
              >
                {GET_STARTED_ITEM.label}
              </Link>
              <button type="button" aria-label={mobileMenuOpen ? "Close menu" : "Open menu"} aria-expanded={mobileMenuOpen} onClick={() => setMobileMenuOpen((open) => !open)} className="grid h-10 w-10 place-items-center rounded-full border border-[var(--mt-line)] bg-white text-[var(--mt-ink-soft)] md:hidden">
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </>
          )}
        </div>
      </div>
      {logoutError ? (
        <p role="alert" className="px-4 pb-2 text-right text-[11px] font-semibold text-[var(--mt-clay-text)]">
          {logoutError}
        </p>
      ) : null}
    </header>
    {mobileMenuOpen ? (
      <div className="fixed inset-x-0 top-14 z-40 border-b border-[var(--mt-line)] bg-white p-3 shadow-lg md:hidden">
        <nav className="grid gap-1.5" aria-label="Mobile menu">
          {NAV_ITEMS.map((item) => (
            <Link key={item.to} to={item.to} onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-4 py-3 text-sm font-bold text-[var(--mt-ink-soft)] hover:bg-[var(--mt-leaf-tint)] hover:text-[var(--mt-leaf-deep)]">
              {item.label}
            </Link>
          ))}
          <div className="my-1 border-t border-[var(--mt-line)]" />
          <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="rounded-xl border border-[var(--mt-line)] px-4 py-3 text-center text-sm font-bold text-[var(--mt-ink-soft)]">Login</Link>
          <Link to="/register" onClick={() => setMobileMenuOpen(false)} className="rounded-xl bg-[var(--mt-leaf)] px-4 py-3 text-center text-sm font-bold text-white">Get Started</Link>
        </nav>
      </div>
    ) : null}
    </>
  );
}
