import { useEffect, useRef, useState } from "react";
import { ChevronDown, Loader2, Mic, Play } from "lucide-react";

import { fetchAuthedMediaBlob } from "@/features/crop-observation/api/cropObservationApi";
import { primary, STRINGS } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

function formatDate(value, locale) {
  try {
    return new Date(value).toLocaleDateString(locale === "or-IN" ? "or-IN" : "en-IN", {
      day: "numeric",
      month: "short",
    });
  } catch {
    return value;
  }
}

function getPhotoIds(media) {
  return [
    ...(media?.crop_condition?.media_ids || []),
    ...(media?.issue_evidence?.media_ids || []),
    ...(media?.practice_evidence?.media_ids || []),
  ];
}

export default function PreviousEntryRow({ entry, locale }) {
  const [open, setOpen] = useState(false);
  const [photoUrls, setPhotoUrls] = useState(null);
  const [voiceUrl, setVoiceUrl] = useState(null);
  const [loadingMedia, setLoadingMedia] = useState(false);
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const createdUrls = useRef([]);

  useEffect(() => {
    const urls = createdUrls.current;
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  async function handleToggle() {
    const next = !open;
    setOpen(next);
    if (!next || photoUrls !== null || loadingMedia) return;

    const media = entry.media || {};
    const photoIds = getPhotoIds(media);
    const voiceId = media.voice_note?.media_id;
    if (!photoIds.length && !voiceId) {
      setPhotoUrls([]);
      return;
    }

    setLoadingMedia(true);
    try {
      const photos = await Promise.all(
        photoIds.map((id) => fetchAuthedMediaBlob(`/v1/crop-observations/media/${id}/content`)),
      );
      const urls = photos.map((blob) => URL.createObjectURL(blob));
      createdUrls.current.push(...urls);
      setPhotoUrls(urls);

      if (voiceId) {
        const blob = await fetchAuthedMediaBlob(`/v1/crop-observations/media/${voiceId}/content`);
        const url = URL.createObjectURL(blob);
        createdUrls.current.push(url);
        setVoiceUrl(url);
      }
    } catch {
      setPhotoUrls([]);
    } finally {
      setLoadingMedia(false);
    }
  }

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      return;
    }
    audio.currentTime = 0;
    audio.play();
  }

  const media = entry.media || {};

  return (
    <div className="rounded-2xl border border-emerald-100 bg-white shadow-sm">
      <button type="button" onClick={handleToggle} className="flex w-full items-center gap-3 px-3 py-3 text-left">
        <div className="min-w-0 flex-1">
          <div className="text-xs font-bold uppercase tracking-[0.22em] text-emerald-700">
            {formatDate(entry.observed_on, locale)}
          </div>
          <div className="mt-1 truncate text-base font-semibold text-slate-900">
            {entry.summary_values?.length ? entry.summary_values.join(" • ") : "—"}
          </div>
          {(media.crop_condition?.count || media.issue_evidence?.count || media.practice_evidence?.count || media.voice_note?.count) ? (
            <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-600">
              {media.crop_condition?.count ? <span>Crop {media.crop_condition.count}</span> : null}
              {media.issue_evidence?.count ? <span>Issue {media.issue_evidence.count}</span> : null}
              {media.practice_evidence?.count ? <span>Action {media.practice_evidence.count}</span> : null}
              {media.voice_note?.count ? (
                <span className="inline-flex items-center gap-1">
                  <Mic className="h-3.5 w-3.5" /> {Math.round(media.voice_note.duration_seconds || 0)}s
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-slate-500 transition-transform", open && "rotate-180")} />
      </button>

      {open ? (
        <div className="border-t border-emerald-50 px-3 py-3">
          {loadingMedia ? (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> {primary(STRINGS.saving, locale)}
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              {(photoUrls || []).map((url, index) => (
                <img key={index} src={url} alt="" className="h-16 w-16 rounded-xl object-cover" />
              ))}
              {voiceUrl ? (
                <button
                  type="button"
                  onClick={togglePlay}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-white"
                  aria-label={primary(STRINGS.replay, locale)}
                >
                  <Play className="h-4 w-4 fill-current" />
                </button>
              ) : null}
              {!photoUrls?.length && !voiceUrl ? (
                <p className="text-sm text-slate-600">{primary(STRINGS.noPreviousEntries, locale)}</p>
              ) : null}
              {voiceUrl ? (
                <audio
                  ref={audioRef}
                  src={voiceUrl}
                  preload="metadata"
                  onPlay={() => setPlaying(true)}
                  onPause={() => setPlaying(false)}
                  onEnded={() => setPlaying(false)}
                  className="hidden"
                />
              ) : null}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
