import { cn } from "@/lib/utils";
import { LoaderCircle, Sprout } from "lucide-react";

function Bar({ className }) {
  return <div className={cn("animate-pulse rounded-lg bg-slate-200/80", className)} />;
}

/** Crop list placeholder — matches CropCard height so there is no layout shift. */
export function CropListSkeleton({ rows = 3 }) {
  return (
    <div className="space-y-4" aria-live="polite" aria-label="Loading your crops">
      <div className="relative overflow-hidden rounded-[24px] border border-[#DCE8D6] bg-[#F1F7ED] px-5 py-5 text-center shadow-sm sm:px-8 sm:py-6">
        <div className="absolute inset-0 animate-pulse bg-[#E5F0DF]/40" />
        <div className="relative flex flex-col items-center justify-center">
          <div className="relative grid h-14 w-14 place-items-center rounded-full bg-[#4B6B3A] text-white shadow-[0_8px_20px_rgba(75,107,58,0.25)]">
            <span className="absolute inset-0 animate-ping rounded-full border border-[#71985C]/50" />
            <Sprout className="h-7 w-7 animate-[bounce_1.8s_ease-in-out_infinite]" />
          </div>
          <p className="mt-3 text-sm font-black text-[#33492A]">Preparing your crop space</p>
          <p className="mt-1 text-xs font-medium text-[#687A60]">Fetching your farms and crop updates…</p>
          <div className="mt-4 flex items-center gap-1.5" aria-hidden="true">
            {[0, 1, 2].map((dot) => <span key={dot} className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#4B6B3A]" style={{ animationDelay: `${dot * 160}ms` }} />)}
          </div>
        </div>
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex min-h-[72px] items-center gap-4 rounded-2xl border border-[#E5E8DF] bg-white px-4 py-3 shadow-[0_5px_18px_rgba(43,61,35,0.04)]">
          <Bar className="h-14 w-14 shrink-0 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Bar className="h-4 w-2/3" />
            <Bar className="h-3 w-1/3" />
          </div>
          <LoaderCircle className="h-4 w-4 animate-spin text-[#9BB88B]" />
        </div>
      ))}
    </div>
  );
}

/** Stage screen placeholder — stage card, status cards, practice grid. */
export function StageScreenSkeleton() {
  return (
    <div className="space-y-6" aria-hidden="true">
      <div className="flex gap-2 overflow-hidden">
        {Array.from({ length: 4 }).map((_, i) => (
          <Bar key={i} className="h-9 w-24 shrink-0 rounded-full" />
        ))}
      </div>
      <Bar className="h-20 w-full rounded-2xl" />
      <div className="space-y-3">
        <Bar className="h-3 w-32" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Bar key={i} className="h-16 w-full rounded-2xl" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Bar key={i} className="h-24 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

export function HistorySkeleton({ rows = 4 }) {
  return (
    <div className="space-y-5" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="space-y-2 border-b border-slate-100 pb-4">
          <Bar className="h-3 w-20" />
          <Bar className="h-4 w-40" />
          <Bar className="h-3 w-24" />
        </div>
      ))}
    </div>
  );
}
