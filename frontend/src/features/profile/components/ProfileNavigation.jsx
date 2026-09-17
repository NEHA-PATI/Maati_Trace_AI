import { motion as Motion } from "framer-motion";

export function ProfileNavigation({
  items,
  activeSection,
  onSelect,
}) {
  return (
    <aside className="mt-fade-up rounded-[1.5rem] border border-slate-200/80 bg-white/95 p-2.5 shadow-[0_12px_30px_rgba(15,23,42,0.06)]">
      <p className="mt-font-mono px-3 pb-2.5 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
        Sections
      </p>
      <nav className="flex flex-col gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            activeSection === item.id;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() =>
                onSelect(item.id)
              }
              aria-current={
                active
                  ? "true"
                  : undefined
              }
              className={`relative flex w-full items-center gap-3 overflow-hidden rounded-xl px-3.5 py-3 text-left text-sm font-semibold transition-all duration-200 ${
                active
                  ? "text-white shadow-[0_8px_18px_rgba(5,150,105,0.22)]"
                  : "text-slate-500 hover:translate-x-0.5 hover:bg-emerald-50/70 hover:text-emerald-800"
              }`}
            >
              {active ? (
                <Motion.div
                  layoutId="profileNavigationActive"
                  className="absolute inset-0 rounded-xl bg-[color:var(--mt-forest-deep)]"
                  transition={{
                    type: "spring",
                    stiffness: 400,
                    damping: 32,
                  }}
                  aria-hidden="true"
                />
              ) : null}
              <span className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${active ? "bg-white/15" : "bg-slate-100"}`}>
                <Icon className="h-4 w-4" />
              </span>
              <span className="relative z-10 whitespace-nowrap">
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
