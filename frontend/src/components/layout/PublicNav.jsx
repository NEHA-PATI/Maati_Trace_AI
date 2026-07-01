import { Link, useLocation } from "react-router-dom";
import { Layers } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Home" },
  { to: "/our-method", label: "Our Method" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/login", label: "Login" },
];

export default function PublicNav() {
  const location = useLocation();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-white/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-6">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
            <Layers className="h-5 w-5" />
          </span>
          <div>
            <div className="text-sm font-black tracking-[0.18em] text-foreground">
              MAATITRACE
            </div>
            <div className="text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
              Land Intelligence
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 md:flex">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.to;

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
      </div>
    </header>
  );
}
