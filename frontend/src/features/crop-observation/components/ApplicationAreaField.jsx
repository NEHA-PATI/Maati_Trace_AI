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
      <div className="grid gap-2.5">
        <button
          type="button"
          aria-pressed={scope === "WHOLE_FARM"}
          onClick={() => onChange({ scope: "WHOLE_FARM" })}
          className={cn(
            "flex min-h-[64px] items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left transition",
            scope === "WHOLE_FARM" ? "border-emerald-600 bg-emerald-50" : "border-slate-200 bg-white hover:border-slate-300",
          )}
        >
          <Sprout className="h-6 w-6 shrink-0 text-emerald-700" />
          <Bilingual pair={STRINGS.wholeFarm} locale={locale} className="font-semibold text-slate-900" />
        </button>

        <button
          type="button"
          aria-pressed={scope === "SELECTED_AREA"}
          onClick={() => onChange({ scope: "SELECTED_AREA", relative_extent: relativeExtent || undefined })}
          className={cn(
            "flex min-h-[64px] items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left transition",
            scope === "SELECTED_AREA" ? "border-emerald-600 bg-emerald-50" : "border-slate-200 bg-white hover:border-slate-300",
          )}
        >
          <MapPin className="h-6 w-6 shrink-0 text-rose-600" />
          <Bilingual pair={STRINGS.selectedArea} locale={locale} className="font-semibold text-slate-900" />
        </button>
      </div>

      {scope === "SELECTED_AREA" ? (
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="mb-2 text-sm text-slate-600">{primary(STRINGS.howMuchFarm, locale)}</p>
          <div className="grid grid-cols-3 gap-2">
            {EXTENTS.map((code) => (
              <button
                key={code}
                type="button"
                aria-pressed={relativeExtent === code}
                onClick={() => onChange({ scope: "SELECTED_AREA", relative_extent: code })}
                className={cn(
                  "min-h-[52px] rounded-xl border-2 px-2 text-xs font-medium leading-tight transition",
                  relativeExtent === code
                    ? "border-emerald-600 bg-emerald-50 text-emerald-800"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300",
                )}
              >
                {primary(RELATIVE_EXTENT_STRINGS[code], locale)}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {field?.help_text ? <p className="text-xs text-slate-500">{field.help_text}</p> : null}
    </div>
  );
}
