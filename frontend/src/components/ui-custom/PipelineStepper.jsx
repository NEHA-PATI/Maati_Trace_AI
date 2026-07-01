import React from "react";
import { Check, Circle, Loader2 } from "lucide-react";

const STATUS_STYLES = {
  completed: "bg-primary text-primary-foreground",
  active: "bg-primary/20 text-primary border border-primary",
  pending: "bg-muted text-muted-foreground",
};

export default function PipelineStepper({ steps, currentStep = 0 }) {
  return (
    <div className="flex items-start gap-0 overflow-x-auto scrollbar-hide py-2">
      {steps.map((step, i) => {
        const status = i < currentStep ? "completed" : i === currentStep ? "active" : "pending";
        return (
          <div key={i} className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center gap-1">
              <div className={`w-7 h-7 rounded-sm flex items-center justify-center text-xs font-display font-bold ${STATUS_STYLES[status]}`}>
                {status === "completed" ? <Check className="w-3.5 h-3.5" /> : 
                 status === "active" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
                 <span>{String(i + 1).padStart(2, "0")}</span>}
              </div>
              <span className={`text-[9px] font-display uppercase tracking-wider text-center max-w-[80px] leading-tight ${status === "active" ? "text-primary font-semibold" : "text-muted-foreground"}`}>
                {step}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`w-8 h-px mx-1 mt-[-12px] ${i < currentStep ? "bg-primary" : "bg-border"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}