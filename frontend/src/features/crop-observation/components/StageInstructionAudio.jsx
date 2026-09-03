import { useEffect, useRef, useState } from "react";
import { Volume2 } from "lucide-react";

import { primary, STRINGS } from "@/features/crop-observation/i18n";

/**
 * Attempts autoplay the moment a stage screen opens (the farmer just
 * tapped into it from the SPA, which usually satisfies the browser's
 * "must follow a user gesture" autoplay rule). When a browser blocks it
 * anyway, a large replay button takes over — there is no reliable trick
 * that guarantees bypassing an autoplay block, so this fallback is the
 * correct production behaviour, not a workaround.
 */
export default function StageInstructionAudio({ src, locale }) {
  const audioRef = useRef(null);
  const [blocked, setBlocked] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    setBlocked(false);
    const audio = audioRef.current;
    if (!audio || !src) return;
    const attempt = audio.play();
    if (attempt?.catch) attempt.catch(() => setBlocked(true));
  }, [src]);

  if (!src) {
    return <p className="text-sm font-medium text-slate-600">{primary(STRINGS.audioUnavailable, locale)}</p>;
  }

  function replay() {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = 0;
    audio.play().then(() => setBlocked(false)).catch(() => setBlocked(true));
  }

  return (
    <div>
      <audio
        ref={audioRef}
        src={src}
        preload="auto"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        className="hidden"
      />
      <button
        type="button"
        onClick={replay}
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
          blocked
            ? "bg-amber-100 text-amber-700"
            : "bg-emerald-100 text-emerald-700"
        }`}
      >
        <Volume2 className="h-3.5 w-3.5" />
        {playing ? primary(STRINGS.listen, locale) + "…" : primary(STRINGS.replay, locale)}
      </button>
    </div>
  );
}
