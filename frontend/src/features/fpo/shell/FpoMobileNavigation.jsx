import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronUp, Menu, X } from "lucide-react";
import { useFpoPortal } from "./FpoPortalContext";
import { getVisibleFpoNavGroups } from "./fpoNavigation";

const shortcuts = [
  ["/fpo/overview", "Overview"],
  ["/fpo/farmers", "Farmers"],
  ["/fpo/monitoring", "Monitoring"],
  ["/fpo/alerts", "Alerts"],
];

export default function FpoMobileNavigation() {
  const { entitlements } = useFpoPortal();
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const groups = getVisibleFpoNavGroups(entitlements);

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isOpen]);

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-slate-950/25 lg:hidden" onClick={() => setIsOpen(false)}>
          <nav
            id="fpo-mobile-more-menu"
            aria-label="All FPO features"
            className="absolute inset-x-3 bottom-20 max-h-[72vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-black text-slate-950">All FPO features</h2>
              <button type="button" onClick={() => setIsOpen(false)} aria-label="Close menu" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-4">
              {groups.map((group) => {
                const items = group.items.filter(({ shortcut }) => !shortcut);
                if (!items.length) return null;
                return (
                  <section key={group.label} aria-label={group.label}>
                    <h3 className="mb-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">{group.label}</h3>
                    <div className="grid grid-cols-2 gap-1">
                      {items.map(({ to, label, icon: Icon }) => {
                        const ItemIcon = Icon;
                        return (
                          <NavLink key={to} to={to} className={({ isActive }) => `flex min-h-10 items-center gap-2 rounded-lg px-2 py-2 text-left text-xs font-bold ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50"}`}>
                            <ItemIcon className="h-4 w-4 shrink-0" />
                            {label}
                          </NavLink>
                        );
                      })}
                    </div>
                  </section>
                );
              })}
            </div>
          </nav>
        </div>
      )}
      <nav aria-label="FPO mobile navigation" className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-5 border-t border-slate-200 bg-white p-2 lg:hidden">
        {shortcuts.map(([to, label]) => {
          const item = groups.flatMap((group) => group.items).find((candidate) => candidate.to === to);
          if (!item) return null;
          return (
            <NavLink key={to} to={to} end={to === "/fpo/overview"} className={({ isActive }) => `rounded-lg py-2 text-center text-[11px] font-bold ${isActive ? "text-emerald-700" : "text-slate-500"}`}>
              {label}
            </NavLink>
          );
        })}
        <button type="button" aria-expanded={isOpen} aria-controls={isOpen ? "fpo-mobile-more-menu" : undefined} onClick={() => setIsOpen((open) => !open)} className={`flex items-center justify-center gap-1 rounded-lg py-2 text-[11px] font-bold ${isOpen ? "text-emerald-700" : "text-slate-500"}`}>
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <Menu className="h-3.5 w-3.5" />}
          More
        </button>
      </nav>
    </>
  );
}
