import React from "react";
import { Check, Clock, ShieldCheck, AlertTriangle } from "lucide-react";

const STYLES = {
  success: {
    chip: "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]",
    Icon: Check,
  },
  warning: {
    chip: "bg-[var(--mt-gold-tint)] text-[var(--mt-gold-text)]",
    Icon: Clock,
  },
  pending: {
    chip: "bg-[var(--mt-gold-tint)] text-[var(--mt-gold-text)]",
    Icon: Clock,
  },
  error: {
    chip: "bg-[var(--mt-clay-tint)] text-[var(--mt-clay-text)]",
    Icon: AlertTriangle,
  },
};

export default function VerificationStamp({ label = "VERIFIED", type = "success", compact = false }) {
  const { chip, Icon } = STYLES[type] || STYLES.success;

  if (compact) {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-bold ${chip}`}>
        <Icon className="h-3 w-3" strokeWidth={2.6} />
        {label}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-[12px] font-bold ${chip}`}>
      {type === "success" ? <ShieldCheck className="h-4 w-4" strokeWidth={2.4} /> : <Icon className="h-4 w-4" strokeWidth={2.4} />}
      {label}
    </span>
  );
}
