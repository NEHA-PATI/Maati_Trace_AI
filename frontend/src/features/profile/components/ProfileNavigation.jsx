export function ProfileNavigation({
  items,
  activeSection,
  onSelect,
}) {
  return (
    <aside className="mt-fade-up rounded-[1.5rem] border border-slate-200 bg-white p-3 shadow-sm">
      <p className="mt-font-mono px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
        Sections
      </p>
      <nav className="flex flex-col gap-1">
        {items.map((item, index) => {
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
              style={{
                "--mt-d": `${index * 45}ms`,
              }}
              className={`mt-fade-up group relative flex w-full items-center gap-3 overflow-hidden rounded-2xl px-3 py-3 text-left text-sm font-bold transition-all duration-300 ${
                active
                  ? "bg-[color:var(--mt-forest-deep)] text-white shadow-[0_10px_24px_rgba(18,51,31,0.28)]"
                  : "text-slate-600 hover:translate-x-0.5 hover:bg-slate-50"
              }`}
            >
              {active ? (
                <span
                  className="absolute inset-y-1.5 left-1.5 w-1 rounded-full bg-[color:var(--mt-harvest)]"
                  aria-hidden="true"
                />
              ) : null}
              <Icon
                className={`h-4 w-4 shrink-0 transition-transform duration-300 ${
                  active
                    ? "scale-110 text-[color:var(--mt-harvest)]"
                    : "text-slate-400 group-hover:text-slate-600"
                }`}
              />
              <span className="relative z-10">
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
