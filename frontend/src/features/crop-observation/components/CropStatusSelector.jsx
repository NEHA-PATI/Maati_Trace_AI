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

function CropStatusSelector({ options, value, onChange, locale, pending }) {
  return (
    <div className="space-y-2.5">
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
              "flex min-h-[64px] w-full items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left font-semibold transition",
              selected ? meta.tone : "border-slate-200 bg-white text-slate-800 hover:border-slate-300",
            )}
          >
            {isPending ? (
              <Loader2 className={cn("h-6 w-6 shrink-0 animate-spin", meta.iconTone)} />
            ) : (
              <Icon className={cn("h-6 w-6 shrink-0", selected ? meta.iconTone : "text-slate-400")} />
            )}
            <Bilingual pair={STATUS_STRINGS[option.code]} locale={locale} />
          </button>
        );
      })}
    </div>
  );
}

export default memo(CropStatusSelector);
