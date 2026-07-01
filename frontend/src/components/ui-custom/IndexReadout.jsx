import React from "react";

export default function IndexReadout({ label, value, unit, min = 0, max = 1, color = "bg-primary", icon }) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {icon && <icon.type {...icon.props} className="w-3 h-3 text-muted-foreground" />}
          <span className="text-[10px] font-display uppercase tracking-widest text-muted-foreground">{label}</span>
        </div>
        <div className="flex items-baseline gap-0.5">
          <span className="text-sm font-display font-bold text-foreground">{typeof value === "number" ? value.toFixed(2) : value}</span>
          {unit && <span className="text-[9px] text-muted-foreground">{unit}</span>}
        </div>
      </div>
      <div className="readout-lane">
        <div className={`absolute inset-y-0 left-0 ${color} transition-all duration-700 rounded-sm`} style={{ width: `${pct}%` }}>
          <div className="absolute right-0 top-0 bottom-0 w-px bg-foreground/20" />
        </div>
      </div>
    </div>
  );
}