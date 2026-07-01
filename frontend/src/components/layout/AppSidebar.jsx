import React from "react";
import { Link, useLocation } from "react-router-dom";

const ITEMS = [
  { to: "/admin", label: "Admin Dashboard" },
  { to: "/my-fpo", label: "My FPO" },
  { to: "/farm-register", label: "Farm Register" },
  { to: "/bulk-upload", label: "Bulk Upload" },
  { to: "/notifications", label: "Notifications" },
  { to: "/use-cases", label: "Use Cases" },
  { to: "/our-method", label: "Our Method" },
];

export default function AppSidebar() {
  const location = useLocation();
  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-card/80 px-3 py-4 lg:block">
      <nav className="space-y-1">
        {ITEMS.map((item) => {
          const active = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`block rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${active ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
