import React from "react";
import { motion } from "framer-motion";

export default function GlassStepLoader({ label = "Loading" }) {
  return (
    <div className="flex items-center gap-3 rounded-3xl border border-white/30 bg-white/70 px-4 py-3 shadow-lg backdrop-blur-xl">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, ease: "linear", duration: 1.2 }}
        className="h-5 w-5 rounded-full border-2 border-emerald-500 border-t-transparent"
      />
      <span className="text-sm font-medium text-slate-700">{label}</span>
    </div>
  );
}
