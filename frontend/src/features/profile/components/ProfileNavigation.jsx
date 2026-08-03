import { motion as Motion } from "framer-motion";

export function ProfileNavigation({
  items,
  activeSection,
  onSelect,
}) {
  return (
    <aside className="mt-fade-up rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_4px_14px_rgba(15,23,42,0.04)]">
      <p className="mt-font-mono px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
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
              className={`relative flex w-full items-center gap-3 overflow-hidden rounded-xl px-3.5 py-2.5 text-left text-sm font-semibold transition-colors duration-200 ${
                active
                  ? "text-white"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              {active ? (
                <Motion.div
                  layoutId="profileNavigationActive"
                  className="absolute inset-0 rounded-xl bg-[color:var(--mt-forest-deep)] shadow-[0_8px_20px_rgba(16,185,129,0.3)]"
                  transition={{
                    type: "spring",
                    stiffness: 400,
                    damping: 32,
                  }}
                  aria-hidden="true"
                />
              ) : null}
              <Icon className="relative z-10 h-4 w-4 shrink-0" />
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
