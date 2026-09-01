import { Camera, Mic } from "lucide-react";

import Bilingual from "@/features/crop-observation/components/Bilingual";
import { PRACTICE_META, STATUS_STRINGS, STRINGS, humanizeCode, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const STATUS_DOT = {
  GOOD: "bg-emerald-500",
  SOME_PROBLEM: "bg-amber-500",
  SERIOUS_PROBLEM: "bg-rose-500",
};

function formatDate(value) {
  try {
    return new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return value;
  }
}

export default function HistoryTimeline({ items, locale }) {
  if (!items.length) {
    return <p className="py-10 text-center text-sm text-slate-500">{primary(STRINGS.noUpdates, locale)}</p>;
  }

  return (
    <ol className="relative space-y-4 border-l-2 border-slate-100 pl-4">
      {items.map((item) => (
        <li key={item.daily_observation_id} className="relative">
          <span
            className={cn(
              "absolute -left-[1.4rem] top-1 h-3 w-3 rounded-full ring-4 ring-slate-50",
              STATUS_DOT[item.crop_status] || "bg-slate-400",
            )}
          />
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            {formatDate(item.date)}
          </div>
          <Bilingual
            as="div"
            className="mt-0.5 text-base font-bold text-slate-950"
            pair={STATUS_STRINGS[item.crop_status]}
            locale={locale}
            primaryText={STATUS_STRINGS[item.crop_status] ? undefined : item.crop_status}
          />
          {item.practices?.length ? (
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {item.practices.map((p) => (
                <span
                  key={p.practice_code}
                  className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600"
                >
                  <span>{PRACTICE_META[p.practice_code]?.icon || "📋"}</span>
                  {PRACTICE_META[p.practice_code]?.en || humanizeCode(p.practice_code)}
                </span>
              ))}
            </div>
          ) : null}
          {item.media_summary?.photos > 0 || item.media_summary?.voice ? (
            <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
              {item.media_summary.photos > 0 ? (
                <span className="inline-flex items-center gap-1">
                  <Camera className="h-3.5 w-3.5" /> {item.media_summary.photos}
                </span>
              ) : null}
              {item.media_summary.voice ? <Mic className="h-3.5 w-3.5" /> : null}
            </div>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
