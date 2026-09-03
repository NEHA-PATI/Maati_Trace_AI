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
    <div className="min-h-screen bg-white">
      <div className="mx-auto flex min-h-screen w-full max-w-[480px] flex-col bg-white">
        <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-[#E9E7DC] bg-white px-3 py-3">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              aria-label="Back"
              className="grid h-12 w-12 shrink-0 place-items-center rounded-[14px] border border-[#E9E7DC] bg-[#F7F8F3] text-[#33492A] active:scale-[0.98]"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
          ) : (
            <span className="w-1" />
          )}
          <div className="min-w-0 flex-1">
            {title ? <div className="truncate text-base font-bold text-[#1D2117]">{title}</div> : null}
            {subtitle ? <div className="truncate text-xs text-[#5B6055]">{subtitle}</div> : null}
          </div>
          {right ? <div className="flex shrink-0 items-center gap-2">{right}</div> : null}
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
    </div>
  );
}
