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

/**
 * One compact "previous entry" row — date + up to 3 summary values + media
 * badges. Tapping it expands photos/voice IN PLACE, fetched only then (never
 * preloaded — see spec "do not preload every old audio recording").
 */
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
    const { photo_media_ids: photoIds = [], voice_media_id: voiceId } = entry.media || {};
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
    if (playing) audio.pause();
    else {
      audio.currentTime = 0;
      audio.play();
    }
  }

  const media = entry.media || {};

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      <button type="button" onClick={handleToggle} className="flex w-full items-center gap-3 px-3 py-2.5 text-left">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-slate-600">
              {formatDate(entry.observed_on, locale)}
            </span>
          </div>
          <div className="mt-0.5 truncate text-base font-semibold text-slate-900">
            {entry.summary_values?.length ? entry.summary_values.join(" • ") : "—"}
          </div>
          {media.photos > 0 || media.voice ? (
            <div className="mt-1 flex items-center gap-3 text-sm font-medium text-slate-700">
              {media.photos > 0 ? <span>📷 {media.photos}</span> : null}
              {media.voice ? (
                <span className="inline-flex items-center gap-1">
                  <Mic className="h-3.5 w-3.5" /> {Math.round(media.voice_duration_seconds || 0)}s
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-slate-500 transition-transform", open && "rotate-180")} />
      </button>

      {open ? (
        <div className="border-t border-slate-100 px-3 py-3">
          {loadingMedia ? (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> {primary(STRINGS.saving, locale)}
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              {(photoUrls || []).map((url, i) => (
                <img key={i} src={url} alt="" className="h-16 w-16 rounded-lg object-cover" />
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
