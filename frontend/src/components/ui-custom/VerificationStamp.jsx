import React from "react";
import { Check, Shield } from "lucide-react";

export default function VerificationStamp({ label = "VERIFIED", type = "success", compact = false }) {
  const colors = {
    success: "border-primary text-primary",
    warning: "border-amber-600 text-amber-600",
    pending: "border-muted-foreground text-muted-foreground",
    error: "border-destructive text-destructive",
  };

  if (compact) {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[9px] font-display font-bold uppercase tracking-widest border rounded-sm ${colors[type]}`}>
        {type === "success" && <Check className="w-2.5 h-2.5" />}
        {label}
      </span>
    );
  }

  return (
    <div className={`stamp-animate inline-flex flex-col items-center gap-1 px-4 py-3 border-2 rounded-sm ${colors[type]} rotate-[-2deg]`}>
      <Shield className="w-5 h-5" />
      <span className="text-[10px] font-display font-bold uppercase tracking-[0.2em]">{label}</span>
    </div>
  );
}