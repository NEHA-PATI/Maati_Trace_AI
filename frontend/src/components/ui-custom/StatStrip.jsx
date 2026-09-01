import React from "react";

const ICON_TINTS = [
  "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]",
  "bg-[var(--mt-sky-tint)] text-[var(--mt-sky-text)]",
  "bg-[var(--mt-gold-tint)] text-[var(--mt-gold-text)]",
  "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]",
  "bg-[var(--mt-clay-tint)] text-[var(--mt-clay-text)]",
  "bg-[var(--mt-sky-tint)] text-[var(--mt-sky-text)]",
];

export default function StatStrip({ items, desktopColumnsClass = "lg:grid-cols-5" }) {
  return (
    <div className={`mt-surface grid grid-cols-2 gap-3 sm:grid-cols-3 ${desktopColumnsClass}`}>
      {items.map((item, i) => {
        const tint = ICON_TINTS[i % ICON_TINTS.length];
        const longValue = typeof item.value === "string" && item.value.length > 4;
        return (
          <div
            key={i}
            className="flex items-center gap-3 rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white px-4 py-4"
          >
            {item.icon && (
              <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${tint}`}>
                <item.icon className="h-5 w-5" strokeWidth={2.1} />
              </div>
            )}
            <div className="min-w-0">
              <div className="flex items-baseline gap-1">
                <span
                  className={`font-extrabold leading-none text-[var(--mt-ink)] ${longValue ? "text-[17px]" : "text-[21px]"}`}
                >
                  {item.value}
                </span>
                {item.unit && (
                  <span className="text-[12px] font-bold text-[var(--mt-ink-faint)]">{item.unit}</span>
                )}
              </div>
              <div className="mt-1 truncate text-[12.5px] font-bold text-[var(--mt-ink-soft)]">{item.label}</div>
              {item.sub && <div className="text-[11px] font-semibold text-[var(--mt-ink-faint)]">{item.sub}</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
