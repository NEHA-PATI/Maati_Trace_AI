import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Responsive crop-observation shell.
 * Mobile keeps the compact sticky header; desktop uses the same component tree
 * inside a wide workspace so the feature no longer looks like a phone mockup.
 */
export default function MobileScreen({ onBack, title, subtitle, right, children, contentClassName }) {
  return (
    <div className="min-h-screen bg-[#F6F7F2]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1320px] flex-col bg-white lg:my-5 lg:min-h-[calc(100vh-2.5rem)] lg:overflow-hidden lg:rounded-[24px] lg:border lg:border-[#E3E8DE] lg:shadow-sm">
        <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-[#E9E7DC] bg-white px-3 py-3 sm:px-5 lg:static">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              aria-label="Back"
              className="grid h-12 w-12 shrink-0 place-items-center rounded-[14px] border border-[#E9E7DC] bg-[#F7F8F3] text-[#33492A] active:scale-[0.98]"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
          ) : <span className="w-1" />}
          <div className="min-w-0 flex-1">
            {title ? <div className="truncate text-base font-bold text-[#1D2117] sm:text-lg">{title}</div> : null}
            {subtitle ? <div className="truncate text-xs text-[#5B6055]">{subtitle}</div> : null}
          </div>
          {right ? <div className="flex shrink-0 items-center gap-2">{right}</div> : null}
        </header>
        <main className={cn("flex-1 pb-[calc(env(safe-area-inset-bottom)+5rem)] lg:pb-6", contentClassName)}>
          {children}
        </main>
      </div>
    </div>
  );
}
