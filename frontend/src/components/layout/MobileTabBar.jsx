import { createElement } from "react";
import { NavLink } from "react-router-dom";
import { LayoutGrid, Sprout, MapPinPlus, Bell, User } from "lucide-react";
import { useAuth } from "@/features/auth/context/useAuth";

const TABS = [
  { to: "/farmer/me", label: "Dashboard", icon: LayoutGrid, color: "#6B7280", activeColor: "#374151", tint: "#F3F4F6" },
  { to: "/my-crops/language", label: "My Crop", icon: Sprout, color: "#65A30D", activeColor: "#3F6212", tint: "#ECFCCB" },
  { to: "/farm-register", label: "Add Farm", icon: MapPinPlus, color: "#0284C7", activeColor: "#075985", tint: "#E0F2FE" },
  { to: "/notifications", label: "Alerts", icon: Bell, color: "#EA580C", activeColor: "#9A3412", tint: "#FFEDD5" },
  { to: "/settings", label: "Account", icon: User, color: "#7C3AED", activeColor: "#5B21B6", tint: "#EDE9FE" },
];

export default function MobileTabBar() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return null;

  return (
    <nav
      aria-label="Main"
      className="mt-surface fixed inset-x-0 bottom-0 z-50 flex items-stretch border-t border-[var(--mt-line)] bg-white/95 backdrop-blur-md md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
    >
      {TABS.map(({ to, label, icon, color, activeColor, tint }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/farmer/me"}
          className={({ isActive }) =>
            `flex flex-1 flex-col items-center justify-center gap-1 px-1 py-2 text-[11px] font-bold ${
              isActive ? "text-[var(--tab-active)]" : "text-[var(--tab-color)]"
            }`
          }
          style={{
            "--tab-color": color,
            "--tab-active": activeColor,
            minHeight: "var(--mt-tap)",
          }}
        >
          {({ isActive }) => (
            <>
              <span
                className={`flex h-8 w-12 items-center justify-center rounded-full ${
                  isActive ? "bg-[var(--tab-tint)]" : "bg-transparent"
                }`}
                style={{ "--tab-tint": tint }}
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
