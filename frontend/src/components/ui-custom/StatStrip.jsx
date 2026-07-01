import React from "react";

const ICON_COLORS = [
  "text-emerald-500 bg-emerald-50",
  "text-blue-500 bg-blue-50",
  "text-violet-500 bg-violet-50",
  "text-amber-500 bg-amber-50",
  "text-rose-500 bg-rose-50",
  "text-cyan-500 bg-cyan-50",
];

export default function StatStrip({ items }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {items.map((item, i) => {
        const colorClass = ICON_COLORS[i % ICON_COLORS.length];
        return (
          <div key={i} className="bg-white border border-gray-100 rounded-2xl px-4 py-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2.5 mb-2">
              {item.icon && (
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${colorClass}`}>
                  <item.icon className="w-4 h-4" />
                </div>
              )}
              <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">{item.label}</span>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-gray-800">{item.value}</span>
              {item.unit && <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{item.unit}</span>}
            </div>
            {item.sub && <span className="text-[10px] text-gray-400 mt-0.5 block">{item.sub}</span>}
          </div>
        );
      })}
    </div>
  );
}