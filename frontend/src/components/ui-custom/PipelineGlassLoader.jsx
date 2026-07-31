import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, Satellite, Grid3x3 } from "lucide-react";

export default function PipelineGlassLoader({ open, title = "Processing pipeline", steps = [], currentStep = 0, status = "", details = [], failure = null, actions = [] }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/45 backdrop-blur-xl"
        >
          <motion.div
            initial={{ scale: 0.96, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            className="w-[min(92vw,760px)] rounded-[32px] border border-white/20 bg-white/10 p-6 text-white shadow-2xl shadow-black/30"
            style={{ boxShadow: "0 20px 80px rgba(0,0,0,0.35)" }}
          >
            <div className="flex items-center gap-4">
              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15">
                <Satellite className="h-7 w-7" />
                <div className="absolute inset-0 animate-pulse rounded-2xl border border-white/20" />
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-white/70">{title}</p>
                <h3 className="mt-1 text-2xl font-black">{status || "Working..."}</h3>
              </div>
            </div>

            {details?.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-white/80">
                {details.map((item) => (
                  <span key={item} className="rounded-full border border-white/15 bg-white/10 px-3 py-1">{item}</span>
                ))}
              </div>
            )}

            <div className="mt-6 grid gap-3">
              {steps.map((step, index) => {
                const done = index < currentStep;
                const active = index === currentStep;
                return (
                  <div key={step} className={`flex items-center gap-3 rounded-2xl border px-4 py-3 ${done ? "border-emerald-300/30 bg-emerald-400/10" : active ? "border-white/20 bg-white/10" : "border-white/10 bg-white/5"}`}>
                    <div className={`flex h-8 w-8 items-center justify-center rounded-full ${done ? "bg-emerald-400 text-slate-950" : active ? "bg-white text-slate-950" : "bg-white/10 text-white/80"}`}>
                      {done ? <Check className="h-4 w-4" /> : active ? <Loader2 className="h-4 w-4 animate-spin" /> : <Grid3x3 className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-semibold">{step}</div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                        <div className={`h-full rounded-full ${done ? "bg-emerald-300" : active ? "bg-white" : "bg-white/20"}`} style={{ width: done ? "100%" : active ? "65%" : "8%" }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {failure && <div className="mt-4 rounded-2xl border border-rose-300/30 bg-rose-500/10 p-3 text-sm text-rose-100">{failure}</div>}

            {actions.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {actions.map((action) => (
                  <button
                    key={action.label}
                    type="button"
                    onClick={action.onClick}
                    className={`rounded-2xl px-4 py-2 text-sm font-semibold transition ${action.variant === "primary" ? "bg-white text-slate-950 hover:bg-white/90" : "border border-white/20 bg-white/10 text-white hover:bg-white/15"}`}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
