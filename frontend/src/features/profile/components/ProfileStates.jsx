import { motion as Motion } from "framer-motion";
import {
  AlertTriangle,
  ShieldAlert,
  Sprout,
} from "lucide-react";

export function ProfileLoading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-[color:var(--mt-paper)] px-4">
      <Motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm rounded-[1.5rem] border border-slate-200 bg-white p-6 text-center shadow-sm"
      >
        <span className="relative mx-auto flex h-12 w-12 items-center justify-center">
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
