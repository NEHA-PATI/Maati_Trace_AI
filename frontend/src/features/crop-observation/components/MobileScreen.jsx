import { ChevronLeft } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Shared phone-first shell for every crop-diary screen: centered ≤ 36rem column,
 * sticky compact header with an optional back button and right-side action slot,
 * safe-area aware bottom padding. Keeps all three farmer pages visually identical.
 */
export default function MobileScreen({
  onBack,
  title,
  subtitle,
  right,
  children,
  contentClassName,
}) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-xl flex-col bg-slate-50">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-slate-100 bg-white/95 px-3 py-2.5 backdrop-blur supports-[backdrop-filter]:bg-white/80">
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            aria-label="Back"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-full text-slate-600 active:bg-slate-100"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
        ) : (
          <span className="w-1" />
        )}
        <div className="min-w-0 flex-1">
          {title ? <div className="truncate text-base font-bold text-slate-950">{title}</div> : null}
          {subtitle ? <div className="truncate text-xs text-slate-500">{subtitle}</div> : null}
        </div>
        {right ? <div className="flex shrink-0 items-center gap-1">{right}</div> : null}
      </header>

      <main
        className={cn(
          "flex-1 px-4 pb-[calc(env(safe-area-inset-bottom)+5rem)] pt-4",
          contentClassName,
        )}
      >
        {children}
      </main>
    </div>
  );
}
