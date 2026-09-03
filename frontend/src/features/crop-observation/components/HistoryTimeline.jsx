import { useRef, useState } from "react";
import { Camera, ChevronDown, Loader2, Mic, Play } from "lucide-react";

import { fetchAuthedMediaBlob } from "@/features/crop-observation/api/cropObservationApi";
import Bilingual from "@/features/crop-observation/components/Bilingual";
import { PRACTICE_META, STATUS_STRINGS, STRINGS, humanizeCode, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const STATUS_DOT = {
  GOOD: "bg-emerald-500",
  SOME_PROBLEM: "bg-amber-500",
  SERIOUS_PROBLEM: "bg-rose-500",
};

function formatDate(value, locale) {
  try {
    return new Date(value).toLocaleDateString(locale === "or-IN" ? "or-IN" : "en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return value;
  }
}

function DayMedia({ summary, locale }) {
  const [open, setOpen] = useState(false);
  const [photoUrls, setPhotoUrls] = useState(null);
  const [voiceUrl, setVoiceUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);
  const created = useRef([]);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (!next || photoUrls !== null) return;
    setLoading(true);
    try {
      const photos = await Promise.all(
        (summary.photo_media_ids || []).map((id) =>
          fetchAuthedMediaBlob(`/v1/crop-observations/media/${id}/content`),
        ),
      );
      const urls = photos.map((blob) => URL.createObjectURL(blob));
      created.current.push(...urls);
      setPhotoUrls(urls);
      if (summary.voice_media_id) {
        const blob = await fetchAuthedMediaBlob(`/v1/crop-observations/media/${summary.voice_media_id}/content`);
        const url = URL.createObjectURL(blob);
        created.current.push(url);
        setVoiceUrl(url);
      }
    } catch {
      setPhotoUrls([]);
    } finally {
      setLoading(false);
    }
  }

  if (!summary || (!summary.photos && !summary.voice)) return null;

  return (
    <div className="mt-2">
      <button type="button" onClick={toggle} className="flex items-center gap-4 text-sm font-medium text-slate-700">
        {summary.photos > 0 ? (
          <span className="inline-flex items-center gap-1">
            <Camera className="h-3.5 w-3.5" /> {summary.photos}
          </span>
        ) : null}
        {summary.voice ? <Mic className="h-3.5 w-3.5" /> : null}
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
      </button>
      {open ? (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin text-slate-400" /> : null}
          {(photoUrls || []).map((url, i) => (
            <img key={i} src={url} alt="" className="h-14 w-14 rounded-lg object-cover" />
          ))}
          {voiceUrl ? (
            <>
              <button
                type="button"
                onClick={() => audioRef.current?.play()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-600 text-white"
                aria-label={primary(STRINGS.replay, locale)}
              >
                <Play className="h-3.5 w-3.5 fill-current" />
              </button>
              <audio ref={audioRef} src={voiceUrl} preload="metadata" className="hidden" />
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default function HistoryTimeline({ items, locale }) {
  if (!items.length) {
    return <p className="py-10 text-center text-base font-medium text-slate-700">{primary(STRINGS.noUpdates, locale)}</p>;
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
          <div className="text-sm font-bold uppercase tracking-wide text-slate-600">
            {formatDate(item.date, locale)}
          </div>
          <Bilingual
            as="div"
            className="mt-0.5 text-lg font-bold text-slate-950"
            pair={STATUS_STRINGS[item.crop_status]}
            primaryText={STATUS_STRINGS[item.crop_status] ? undefined : item.crop_status}
            locale={locale}
          />
          {item.practices?.length ? (
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {item.practices.map((p) => (
                <span
                  key={p.practice_code}
                  className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-sm font-semibold text-slate-800"
                >
                  <span>{PRACTICE_META[p.practice_code]?.icon || "📋"}</span>
                  {humanizeCode(p.practice_code)}
                </span>
              ))}
            </div>
          ) : null}
          <DayMedia summary={item.media_summary} locale={locale} />
        </li>
      ))}
    </ol>
  );
}
