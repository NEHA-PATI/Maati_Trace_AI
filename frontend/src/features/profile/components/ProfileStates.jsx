import { motion as Motion } from "framer-motion";
import {
  AlertTriangle,
  ShieldAlert,
  Sprout,
  Sparkles,
} from "lucide-react";

export function ProfileLoading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center overflow-hidden bg-[color:var(--mt-paper)] px-4">
      <Motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm rounded-[1.5rem] border border-slate-200 bg-white p-6 text-center shadow-sm"
      >
        <div className="relative mx-auto h-36 w-32" aria-hidden="true">
          <Motion.div
            className="absolute left-1/2 top-0 z-10 -translate-x-1/2"
            animate={{ y: [0, -10, -150], rotate: [0, -5, 8], opacity: [1, 1, 0] }}
            transition={{ duration: 2.2, times: [0, 0.42, 1], repeat: Infinity, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="relative flex flex-col items-center">
              <div className="absolute -top-2 h-3 w-16 rounded-full bg-[color:var(--mt-harvest)] shadow-sm" />
              <div className="absolute -top-5 h-6 w-9 rounded-t-full bg-[color:var(--mt-harvest-deep)]" />
              <div className="relative mt-1 flex h-12 w-12 items-center justify-center rounded-[45%] border-2 border-amber-900/10 bg-amber-200 shadow-md">
                <span className="absolute left-3 top-5 h-1.5 w-1.5 rounded-full bg-slate-700" />
                <span className="absolute right-3 top-5 h-1.5 w-1.5 rounded-full bg-slate-700" />
                <span className="absolute bottom-2 h-1.5 w-4 rounded-full border-b-2 border-rose-500" />
              </div>
              <div className="-mt-1 h-11 w-14 rounded-t-2xl rounded-b-lg bg-[color:var(--mt-forest-deep)] shadow-md" />
              <div className="flex gap-3"><span className="h-6 w-3 rounded-b-full bg-slate-700" /><span className="h-6 w-3 rounded-b-full bg-slate-700" /></div>
            </div>
          </Motion.div>
          <Motion.div className="absolute left-1 top-12 text-[color:var(--mt-harvest)]" animate={{ y: [0, -8, 0], rotate: [0, 20, -10, 0], opacity: [0, 1, 0] }} transition={{ duration: 1.8, repeat: Infinity, delay: 0.3 }}><Sparkles className="h-5 w-5" /></Motion.div>
          <Motion.div className="absolute right-1 top-5 text-[color:var(--mt-forest)]" animate={{ y: [8, -8, 8], rotate: [0, -25, 0], opacity: [0, 1, 0] }} transition={{ duration: 1.8, repeat: Infinity, delay: 0.7 }}><Sprout className="h-5 w-5" /></Motion.div>
          <Motion.div className="absolute bottom-1 left-1/2 h-3 w-24 -translate-x-1/2 rounded-full bg-[color:var(--mt-forest-soft)] blur-sm" animate={{ scaleX: [1, 0.7, 1], opacity: [0.7, 0.25, 0.7] }} transition={{ duration: 1.1, repeat: Infinity }} />
        </div>
        <span className="relative mx-auto -mt-2 flex h-12 w-12 items-center justify-center">
          <span
            className="absolute inset-0 animate-ping rounded-full bg-[color:var(--mt-forest-soft)]"
            aria-hidden="true"
          />
          <span className="relative flex h-12 w-12 items-center justify-center rounded-full bg-[color:var(--mt-forest-deep)]">
            <Sprout className="h-6 w-6 text-lime-200" />
          </span>
        </span>
        <p className="mt-font-display mt-4 text-base font-semibold text-slate-800">
          Loading your profile...
        </p>
        <div
          className="mt-5 space-y-2.5"
          aria-hidden="true"
        >
          <div className="mt-shimmer relative h-3 w-full overflow-hidden rounded-full bg-slate-100" />
          <div className="mt-shimmer relative h-3 w-4/5 overflow-hidden rounded-full bg-slate-100" />
          <div className="mt-shimmer relative h-3 w-2/3 overflow-hidden rounded-full bg-slate-100" />
        </div>
      </Motion.div>
    </div>
  );
}

export function ProfileLoadError({
  error,
  onRetry,
}) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-[color:var(--mt-paper)] px-4">
      <Motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="max-w-md rounded-[1.5rem] border border-rose-100 bg-white p-6 text-center shadow-sm"
      >
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[color:var(--mt-rose-soft)]">
          <AlertTriangle className="h-7 w-7 text-[color:var(--mt-rose)]" />
        </span>
        <h1 className="mt-font-display mt-4 text-xl font-semibold text-slate-950">
          Profile could not load
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {error?.message
            || "Please try again."}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-5 rounded-2xl bg-[color:var(--mt-forest-deep)] px-5 py-3 text-sm font-bold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[color:var(--mt-forest)]"
        >
          Retry
        </button>
      </Motion.div>
    </div>
  );
}

export function UnsupportedProfileRole({
  role,
}) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-[color:var(--mt-paper)] px-4">
      <Motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="max-w-md rounded-[1.5rem] border border-amber-100 bg-white p-6 text-center shadow-sm"
      >
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[color:var(--mt-harvest-soft)]">
          <ShieldAlert className="h-7 w-7 text-[color:var(--mt-harvest)]" />
        </span>
        <h1 className="mt-font-display mt-4 text-xl font-semibold text-slate-950">
          Profile settings unavailable
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          The current role does not have a profile editor yet.
        </p>
        <p className="mt-font-mono mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-xs font-bold text-slate-500">
          Role: {role || "unknown"}
        </p>
      </Motion.div>
    </div>
  );
}
