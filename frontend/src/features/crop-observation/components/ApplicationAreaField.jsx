import { MapPin, Sprout } from "lucide-react";

import Bilingual from "@/features/crop-observation/components/Bilingual";
import { RELATIVE_EXTENT_STRINGS, STRINGS, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const EXTENTS = ["SMALL_PART", "ABOUT_HALF", "MOST_OF_FARM"];

/** Mutually-exclusive scope choice rendered as large tappable cards, not
 * checkboxes — "Selected Area" must read as a deliberate choice. */
export default function ApplicationAreaField({ field, value, onChange, locale }) {
  const scope = value?.scope || null;
  const relativeExtent = value?.relative_extent || null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2.5">
        <button
          type="button"
          aria-pressed={scope === "WHOLE_FARM"}
          onClick={() => onChange({ scope: "WHOLE_FARM" })}
          className={cn(
            "flex min-h-[76px] flex-col items-center justify-center gap-1.5 rounded-[14px] border-2 px-2 py-3 text-center transition",
            scope === "WHOLE_FARM" ? "border-[#4B6B3A] bg-[#E1F1D6]" : "border-[#E9E7DC] bg-white hover:border-[#C9D8BD]",
          )}
        >
          <Sprout className="h-5 w-5 shrink-0 text-[#33492A]" />
          <Bilingual pair={STRINGS.wholeFarm} locale={locale} className="text-sm font-bold leading-tight text-[#1D2117]" />
        </button>

        <button
          type="button"
          aria-pressed={scope === "SELECTED_AREA"}
          onClick={() => onChange({ scope: "SELECTED_AREA", relative_extent: relativeExtent || undefined })}
          className={cn(
            "flex min-h-[76px] flex-col items-center justify-center gap-1.5 rounded-[14px] border-2 px-2 py-3 text-center transition",
            scope === "SELECTED_AREA" ? "border-[#4B6B3A] bg-[#E1F1D6]" : "border-[#E9E7DC] bg-white hover:border-[#C9D8BD]",
          )}
        >
          <MapPin className="h-5 w-5 shrink-0 text-[#33492A]" />
          <Bilingual pair={STRINGS.selectedArea} locale={locale} className="text-sm font-bold leading-tight text-[#1D2117]" />
        </button>
      </div>

      {scope === "SELECTED_AREA" ? (
        <div className="rounded-2xl bg-[#F1F5EA] p-3">
          <p className="mb-2 text-sm font-semibold text-[#1D2117]">{primary(STRINGS.howMuchFarm, locale)}</p>
          <div className="grid grid-cols-3 gap-2">
            {EXTENTS.map((code) => (
              <button
                key={code}
                type="button"
                aria-pressed={relativeExtent === code}
                onClick={() => onChange({ scope: "SELECTED_AREA", relative_extent: code })}
                className={cn(
                  "min-h-[52px] rounded-xl border-2 px-2 text-sm font-bold leading-tight transition",
                  relativeExtent === code
                    ? "border-[#4B6B3A] bg-[#E1F1D6] text-[#33492A]"
                    : "border-[#E9E7DC] bg-white text-[#1D2117] hover:border-[#C9D8BD]",
                )}
              >
                {primary(RELATIVE_EXTENT_STRINGS[code], locale)}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {field?.help_text ? <p className="text-sm text-slate-700">{field.help_text}</p> : null}
    </div>
  );
}
