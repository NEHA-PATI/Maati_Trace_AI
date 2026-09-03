import { useEffect, useRef, useState } from "react";
import { Camera, ChevronDown, Loader2, Mic, Play } from "lucide-react";

import { fetchAuthedMediaBlob } from "@/features/crop-observation/api/cropObservationApi";
import Bilingual from "@/features/crop-observation/components/Bilingual";
import { iconForPractice } from "@/features/crop-observation/components/fieldIcons";
import { STATUS_STRINGS, STRINGS, humanizeCode, primary } from "@/features/crop-observation/i18n";
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

function getPhotoIds(summary) {
  return [
    ...(summary?.crop_condition?.media_ids || []),
    ...(summary?.issue_evidence?.media_ids || []),
    ...(summary?.practice_evidence?.media_ids || []),
  ];
}

function DayMedia({ summary, locale }) {
  const [open, setOpen] = useState(false);
  const [photoUrls, setPhotoUrls] = useState(null);
  const [voiceUrl, setVoiceUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);
  const created = useRef([]);

  useEffect(() => () => created.current.forEach((url) => URL.revokeObjectURL(url)), []);

  const cropCount = summary?.crop_condition?.count || 0;
  const issueCount = summary?.issue_evidence?.count || 0;
  const practiceCount = summary?.practice_evidence?.count || 0;
  const voiceCount = summary?.voice_note?.count || 0;

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (!next || photoUrls !== null) return;
    setLoading(true);
    try {
      const photos = await Promise.all(
        getPhotoIds(summary).map((id) => fetchAuthedMediaBlob(`/v1/crop-observations/media/${id}/content`)),
      );
      const urls = photos.map((blob) => URL.createObjectURL(blob));
      created.current.push(...urls);
      setPhotoUrls(urls);
      if (summary.voice_note?.media_id) {
        const blob = await fetchAuthedMediaBlob(`/v1/crop-observations/media/${summary.voice_note.media_id}/content`);
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

  if (!summary || (!cropCount && !issueCount && !practiceCount && !voiceCount)) return null;

  return (
    <div className="mt-3">
      <button type="button" onClick={toggle} className="flex flex-wrap items-center gap-3 text-sm font-semibold text-[#5B6055]">
        {cropCount ? <span className="inline-flex items-center gap-1"><Camera className="h-3.5 w-3.5" /> Crop {cropCount}</span> : null}
        {issueCount ? <span>Issue {issueCount}</span> : null}
        {practiceCount ? <span>Action {practiceCount}</span> : null}
        {voiceCount ? <span className="inline-flex items-center gap-1"><Mic className="h-3.5 w-3.5" /> Voice</span> : null}
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
      </button>
      {open ? (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin text-[#5B6055]" /> : null}
          {(photoUrls || []).map((url, index) => (
            <img key={index} src={url} alt="" className="h-14 w-14 rounded-lg object-cover" />
          ))}
          {voiceUrl ? (
            <>
              <button
                type="button"
                onClick={() => audioRef.current?.play()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-[#4B6B3A] text-white"
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
    return <p className="py-10 text-center text-base font-medium text-[#5B6055]">{primary(STRINGS.noUpdates, locale)}</p>;
  }

  return (
    <ol className="relative space-y-4 border-l-2 border-[#C9D8BD] pl-4">
      {items.map((item) => (
        <li key={item.daily_observation_id} className="relative">
          <span
            className={cn(
              "absolute -left-[1.4rem] top-1 h-3 w-3 rounded-full ring-4 ring-[#F7F8F3]",
              STATUS_DOT[item.crop_status] || "bg-slate-400",
            )}
          />
          <div className="text-sm font-bold text-[#4B6B3A]">{formatDate(item.date, locale)}</div>
          <Bilingual
            as="div"
            className="mt-0.5 text-lg font-bold text-[#1D2117]"
            pair={STATUS_STRINGS[item.crop_status]}
            primaryText={STATUS_STRINGS[item.crop_status] ? undefined : item.crop_status}
            locale={locale}
          />
          {item.practices?.length ? (
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {item.practices.map((practice) => {
                const PracticeIcon = iconForPractice(practice.practice_code);
                return (
                  <span
                    key={practice.practice_code}
                    className="inline-flex items-center gap-1 rounded-full bg-[#E1F1D6] px-2.5 py-1 text-xs font-bold text-[#33492A]"
                  >
                    <PracticeIcon className="h-3.5 w-3.5" />
                    {humanizeCode(practice.practice_code)}
                  </span>
                );
              })}
            </div>
          ) : null}
          <DayMedia summary={item.media_summary} locale={locale} />
        </li>
      ))}
    </ol>
  );
}
