import { Link, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Home" },
  { to: "/our-method", label: "Our Method" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/login", label: "Login" },
];

const GET_STARTED_ITEM = { to: "/register", label: "Get Started" };

export default function PublicNav() {
  const location = useLocation();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-white/85 backdrop-blur-md">
      <div className="flex items-center justify-between px-4 py-3 md:px-6">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f4f0df] shadow-sm ring-1 ring-black/10">
            <img src="/MaatiAI.png" alt="MaatiTrace logo" className="h-7 w-7 object-contain" />
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

          <Link
            to={GET_STARTED_ITEM.to}
            className="rounded-full bg-primary px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
          >
            {GET_STARTED_ITEM.label}
          </Link>
        </nav>
      </div>
    </header>
  );
}
