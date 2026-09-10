import { createElement } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { LayoutGrid, Sprout, MapPinPlus, Bell, User } from "lucide-react";

const TABS = [
  { to: "/farmer/me", label: "Dashboard", icon: LayoutGrid },
  { to: "/my-crops/language", label: "My Crop", icon: Sprout },
  { to: "/farm-register", label: "Add Farm", icon: MapPinPlus },
  { to: "/notifications", label: "Alerts", icon: Bell },
  { to: "/settings", label: "Account", icon: User },
];

export default function MobileTabBar() {
  const { pathname } = useLocation();
  if (pathname.startsWith("/farm-register")) return null;

  return (
    <nav
      aria-label="Main"
      className="mt-surface fixed inset-x-0 bottom-0 z-50 flex items-stretch border-t border-[var(--mt-line)] bg-white/95 backdrop-blur-md md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
    >
      {TABS.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/farmer/me"}
          className={({ isActive }) =>
            `flex flex-1 flex-col items-center justify-center gap-1 px-1 py-2 text-[11px] font-bold ${
              isActive ? "text-[var(--mt-leaf-deep)]" : "text-[var(--mt-ink-faint)]"
            }`
          }
          style={{ minHeight: "var(--mt-tap)" }}
        >
          {({ isActive }) => (
            <>
              <span
                className={`flex h-8 w-12 items-center justify-center rounded-full ${
                  isActive ? "bg-[var(--mt-leaf-tint)]" : "bg-transparent"
                }`}
              >
                {createElement(icon, { className: "h-[18px] w-[18px]", strokeWidth: 2.2 })}
              </span>
              {label}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
