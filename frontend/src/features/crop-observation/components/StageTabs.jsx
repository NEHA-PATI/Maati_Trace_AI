import { memo, useEffect, useRef } from "react";
import { Flower2, Leaf, Package, Sprout, Sun, Tractor, Trees, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Horizontally scrollable stage rail. Past stages get a check, the current stage
 * is filled, upcoming stages are muted — so the farmer can see crop progress at
 * a glance. Auto-scrolls the current stage into view on mount.
 */
function StageTabs({ tabs, activeStageCode, onSelect }) {
  const railRef = useRef(null);
  const currentRef = useRef(null);

  useEffect(() => {
    currentRef.current?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
  }, [activeStageCode]);

  const currentIndex = tabs.findIndex((t) => t.stage_code === activeStageCode);
  const stageIcons = [Leaf, Sprout, Wheat, Flower2, Sun, Tractor, Package, Trees];
  const iconColors = ["text-[#4B8B3B]", "text-[#68A357]", "text-[#D49A24]", "text-[#F4B400]", "text-[#E28A16]", "text-[#72A944]", "text-[#4A7C59]", "text-[#D9822B]"];

  return (
    <div ref={railRef} className="flex w-full max-w-full flex-nowrap gap-2 overflow-x-auto overflow-y-hidden overscroll-x-contain border-b border-[#E9E7DC] bg-[#FBFCF8] px-4 py-2.5 touch-pan-x scroll-smooth [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:gap-1.5 sm:overflow-visible sm:justify-center">
      {tabs.map((tab, index) => {
        const selected = tab.stage_code === activeStageCode;
        const done = currentIndex > -1 && index < currentIndex;
        const StageIcon = stageIcons[index] || Trees;
        return (
          <button
            key={tab.stage_code}
            ref={selected ? currentRef : null}
            type="button"
            onClick={() => onSelect(tab.stage_code)}
            className={cn(
              "flex min-h-[52px] shrink-0 snap-start items-center justify-center rounded-[15px] border px-4 text-[15px] font-semibold whitespace-nowrap transition-all duration-300 active:scale-[0.98] sm:min-w-0 sm:flex-1 sm:px-2 sm:text-[13px]",
              selected && "border-[#2F6B35] bg-[#2F6B35] text-white shadow-[0_4px_10px_rgba(47,107,53,0.25)]",
              done && !selected && "border-[#DCE8D6] bg-[#F4F8F1] text-[#426333]",
              !selected && !done && "border-[#E6E3DD] bg-white text-[#53604E] hover:border-[#B8CEA9] hover:bg-[#F8FBF6]",
            )}
          >
            <StageIcon strokeWidth={2.5} className={cn("mr-2 h-5 w-5 shrink-0 sm:mr-1 sm:h-4 sm:w-4", selected ? "text-white" : iconColors[index] || "text-[#4B8B3B]")} />
            {tab.name}
          </button>
        );
      })}
    </div>
  );
}

export default memo(StageTabs);
