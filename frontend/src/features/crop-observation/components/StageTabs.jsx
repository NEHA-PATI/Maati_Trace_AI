import { memo, useEffect, useRef } from "react";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Horizontally scrollable stage rail. Past stages get a check, the current stage
 * is filled, upcoming stages are muted — so the farmer can see crop progress at
 * a glance. Auto-scrolls the current stage into view on mount.
 */
function StageTabs({ tabs, onSelect }) {
  const railRef = useRef(null);
  const currentRef = useRef(null);

  useEffect(() => {
    currentRef.current?.scrollIntoView({ inline: "center", block: "nearest", behavior: "auto" });
  }, []);

  const currentIndex = tabs.findIndex((t) => t.is_current);

  return (
    <div ref={railRef} className="flex gap-2 overflow-x-auto px-4 py-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {tabs.map((tab, index) => {
        const done = currentIndex > -1 && index < currentIndex;
        return (
          <button
            key={tab.stage_code}
            ref={tab.is_current ? currentRef : null}
            type="button"
            onClick={() => onSelect(tab.stage_code)}
            className={cn(
              "flex min-h-[44px] shrink-0 items-center gap-1.5 rounded-full border-2 px-4 text-sm font-semibold whitespace-nowrap transition",
              tab.is_current && "border-emerald-600 bg-emerald-600 text-white",
              done && "border-emerald-200 bg-emerald-50 text-emerald-700",
              !tab.is_current && !done && "border-slate-200 bg-white text-slate-500",
            )}
          >
            {done ? <Check className="h-3.5 w-3.5" /> : <span className="opacity-60">{index + 1}.</span>}
            {tab.name}
          </button>
        );
      })}
    </div>
  );
}

export default memo(StageTabs);
