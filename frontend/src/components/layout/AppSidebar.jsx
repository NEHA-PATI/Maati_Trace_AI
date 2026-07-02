import React from "react";
import { Link, useLocation } from "react-router-dom";
import { getStoredUser } from "@/lib/auth/session";
import { getSidebarItemsForRole } from "@/lib/rbac/permissions";

export default function AppSidebar() {
  const location = useLocation();
  const user = getStoredUser();
  const items = getSidebarItemsForRole(user?.role);
  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-card/80 px-3 py-4 lg:block">
      <nav className="space-y-1">
        {items.map((item) => {
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
