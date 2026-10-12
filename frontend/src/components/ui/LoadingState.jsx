import { LoaderCircle } from "lucide-react";

export default function LoadingState({ label = "Loading…", className = "" }) {
  return (
    <div className={`flex items-center gap-3 ${className}`} role="status" aria-live="polite">
      <span className="relative grid h-9 w-9 shrink-0 place-items-center rounded-full bg-emerald-50 text-emerald-600 shadow-sm">
        <span className="absolute inset-0 animate-ping rounded-full bg-emerald-200/60" />
        <LoaderCircle className="relative h-5 w-5 animate-spin" strokeWidth={2.5} />
      </span>
      <span className="flex flex-col gap-1">
        <span className="text-sm font-semibold text-slate-600">{label}</span>
        <span className="h-1.5 w-28 overflow-hidden rounded-full bg-slate-100"><span className="loading-progress-bar block h-full w-1/2 rounded-full bg-emerald-500" /></span>
      </span>
    </div>
  );
}
