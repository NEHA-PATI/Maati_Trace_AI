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
    <div className="grid grid-cols-3 gap-2.5">
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
              "flex min-h-[76px] w-full flex-col items-center justify-center gap-1.5 rounded-2xl border-2 px-2 py-3 text-center text-xs font-bold leading-tight transition active:scale-[0.98]",
              selected ? meta.tone : "border-[#E9E7DC] bg-white text-[#5B6055] hover:border-[#C9D8BD]",
            )}
          >
            {isPending ? (
              <Loader2 className={cn("h-6 w-6 shrink-0 animate-spin", meta.iconTone)} />
            ) : (
              <Icon className={cn("h-6 w-6 shrink-0", selected ? meta.iconTone : "text-[#5B6055]")} />
            )}
            <Bilingual pair={STATUS_STRINGS[option.code]} locale={locale} className="max-w-full break-words" />
          </button>
        );
      })}
    </div>
  );
}

export default memo(CropStatusSelector);
