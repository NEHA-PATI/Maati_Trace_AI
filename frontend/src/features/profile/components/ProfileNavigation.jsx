import { motion as Motion } from "framer-motion";

export function ProfileNavigation({
  items,
  activeSection,
  onSelect,
}) {
  return (
    <aside className="mt-fade-up rounded-[1.25rem] border border-[#E3E8DE] bg-white p-1.5 shadow-[0_10px_24px_rgba(43,61,35,0.06)]">
      <p className="mt-font-mono px-2 pb-1 text-[8px] font-semibold uppercase tracking-[0.16em] text-[#91A087]">
        Sections
      </p>
      <nav className="grid grid-cols-2 gap-1 sm:grid-cols-3 lg:flex lg:flex-col lg:gap-0.5">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            activeSection === item.id;
          const iconColor = {
            account: "text-[#0F9F75]",
            organisation: "text-[#0F9F75]",
            identity: "text-[#7C3AED]",
            contact: "text-[#2563EB]",
            location: "text-[#E06B2D]",
            role: "text-[#65A30D]",
            operations: "text-[#CA8A04]",
            consent: "text-[#DB2777]",
            verification: "text-[#0891B2]",
            export: "text-[#EA580C]",
          }[item.id] || "text-[#4B6B3A]";

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
              className={`relative flex min-w-0 w-full items-center gap-2 overflow-hidden rounded-lg px-2 py-2 text-left text-xs font-semibold transition-all duration-200 ${
                active
                  ? "text-white shadow-[0_8px_18px_rgba(5,150,105,0.22)]"
                  : "text-[#687064] hover:translate-x-0.5 hover:bg-[#F2F7EE] hover:text-[#4B6B3A]"
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
              <span className={`relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${active ? "bg-white/15" : "bg-[#F1F5EF]"}`}>
                <Icon className={`h-3.5 w-3.5 ${active ? "text-white" : iconColor}`} strokeWidth={2.1} />
              </span>
              <span className="relative z-10 truncate">
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
