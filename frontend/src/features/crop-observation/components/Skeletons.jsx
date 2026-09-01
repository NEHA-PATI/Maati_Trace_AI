import { cn } from "@/lib/utils";

function Bar({ className }) {
  return <div className={cn("animate-pulse rounded-lg bg-slate-200/80", className)} />;
}

/** Crop list placeholder — matches CropCard height so there is no layout shift. */
export function CropListSkeleton({ rows = 3 }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex min-h-[72px] items-center gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <Bar className="h-14 w-14 shrink-0 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Bar className="h-4 w-2/3" />
            <Bar className="h-3 w-1/3" />
          </div>
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
