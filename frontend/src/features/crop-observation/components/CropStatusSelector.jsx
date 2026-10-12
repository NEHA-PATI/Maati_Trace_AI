import { memo } from "react";
import { AlertTriangle, Check, Loader2, OctagonAlert } from "lucide-react";

import Bilingual from "@/features/crop-observation/components/Bilingual";
import { STATUS_STRINGS } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const STATUS_META = {
  GOOD: {
    icon: Check,
    tone: "border-emerald-600 bg-emerald-50 text-emerald-900",
    iconTone: "text-emerald-600",
  },
  SOME_PROBLEM: {
    icon: AlertTriangle,
    tone: "border-amber-500 bg-amber-50 text-amber-900",
    iconTone: "text-amber-600",
  },
  SERIOUS_PROBLEM: {
    icon: OctagonAlert,
    tone: "border-rose-600 bg-rose-50 text-rose-900",
    iconTone: "text-rose-600",
  },
};

const STATUS_DESCRIPTIONS = {
  GOOD: "Healthy crop, normal growth.",
  SOME_PROBLEM: "Minor issues need attention.",
  SERIOUS_PROBLEM: "Critical issues need action.",
};

function CropStatusSelector({ options, value, onChange, locale, pending }) {
  return (
    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
      {options.map((option) => {
        const meta = STATUS_META[option.code];
        if (!meta) return null;
        const Icon = meta.icon;
        const selected = value === option.code;
        const isPending = pending === option.code;
        return (
          <button
            key={option.code}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(option.code)}
            className={cn(
              "flex min-h-[92px] w-full items-center gap-4 rounded-2xl border-2 px-4 py-3 text-left transition-all duration-200 active:scale-[0.98] sm:px-6",
              selected ? meta.tone : "border-[#E9E7DC] bg-white text-[#5B6055] hover:border-[#C9D8BD] hover:shadow-sm",
            )}
          >
            <span className={cn("grid h-14 w-14 shrink-0 place-items-center rounded-full", option.code === "GOOD" ? "bg-emerald-100" : option.code === "SOME_PROBLEM" ? "bg-amber-100" : "bg-rose-100")}>
              {isPending ? <Loader2 className={cn("h-7 w-7 animate-spin", meta.iconTone)} /> : <Icon className={cn("h-7 w-7", meta.iconTone)} />}
            </span>
            <span className="min-w-0">
              <Bilingual pair={STATUS_STRINGS[option.code]} locale={locale} className="block max-w-full break-words text-sm font-bold sm:text-base" />
              <span className="mt-1 block text-xs font-medium leading-4 text-[#687064]">{STATUS_DESCRIPTIONS[option.code]}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default memo(CropStatusSelector);
