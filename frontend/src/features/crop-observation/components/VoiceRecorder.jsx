import { useEffect, useRef, useState } from "react";
import { Mic, Play, Square, Trash2 } from "lucide-react";

import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const MAX_SECONDS = 60;
const PREFERRED_TYPES = ["audio/webm", "audio/ogg", "audio/mp4"];

function pickMimeType() {
  if (typeof MediaRecorder === "undefined") return null;
  return PREFERRED_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

function formatSeconds(total) {
  const m = Math.floor(total / 60);
  const s = Math.floor(total % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function Wave({ active = false }) {
  return (
    <div className="flex h-7 items-center gap-1">
      {Array.from({ length: 20 }).map((_, index) => (
        <i
          key={index}
          className={cn("block w-[3px] rounded-full", active ? "bg-rose-300" : "bg-[#C9D8BD]")}
          style={{ height: `${8 + ((index * 7) % 20)}px` }}
        />
      ))}
    </div>
  );
}

export default function VoiceRecorder({ value, onChange, locale, title, maxSeconds = MAX_SECONDS }) {
  const [status, setStatus] = useState(value ? "recorded" : "idle");
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const previewUrlRef = useRef(null);
  const secondsRef = useRef(0);

  useEffect(() => {
    return () => {
      window.clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    };
  }, []);

  useEffect(() => {
    if (!value) {
      setStatus("idle");
      return;
    }
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = URL.createObjectURL(value);
    setStatus("recorded");
  }, [value]);

  async function startRecording() {
    setError("");
    setStatus("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const extension = (recorder.mimeType || "audio/webm").includes("mp4") ? "m4a" : "webm";
        const file = new File([blob], `voice-note.${extension}`, { type: blob.type });
        onChange(file, secondsRef.current);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setStatus("recording");
      setSeconds(0);
      secondsRef.current = 0;
      timerRef.current = window.setInterval(() => {
        setSeconds((prev) => {
          const next = prev + 1;
          secondsRef.current = next;
          if (next >= maxSeconds) stopRecording();
          return next;
        });
      }, 1000);
    } catch {
      setStatus("idle");
      setError(locale === "or-IN" ? "Could not access the microphone." : "Could not access the microphone.");
    }
  }

  function stopRecording() {
    window.clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    setStatus("recorded");
  }

  function handleDelete() {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = null;
    onChange(null, 0);
    setStatus("idle");
    setSeconds(0);
    secondsRef.current = 0;
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

  return (
    <div>
      <div className="text-sm font-bold text-[#1D2117]">{title || primary(STRINGS.recordVoice, locale)}</div>
      <div className="mt-2 rounded-[14px] border border-[#E9E7DC] bg-[#F7F8F3] p-3">
        {status === "idle" || status === "requesting" ? (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={startRecording}
              disabled={status === "requesting"}
              className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-full bg-[#4B6B3A] text-white shadow-md shadow-emerald-100 transition active:scale-[0.98] disabled:opacity-60"
              aria-label={primary(STRINGS.recordVoice, locale)}
            >
              <Mic className="h-5 w-5" />
            </button>
            <div className="min-w-0 flex-1">
              <Wave />
              <p className="text-xs font-semibold text-[#5B6055]">{primary(STRINGS.recordVoice, locale)}</p>
            </div>
          </div>
        ) : null}

        {status === "recording" ? (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={stopRecording}
              className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-full bg-rose-600 text-white shadow-md shadow-rose-200"
              aria-label={primary(STRINGS.stopRecording, locale)}
            >
              <Square className="h-5 w-5 fill-current" />
            </button>
            <div className="min-w-0 flex-1 text-rose-600">
              <Wave active />
              <span className="text-sm font-bold tabular-nums">
                {formatSeconds(seconds)} / {formatSeconds(maxSeconds)}
              </span>
            </div>
          </div>
        ) : null}

        {status === "recorded" && value ? (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={togglePlay}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#4B6B3A] text-white"
              aria-label={primary(STRINGS.replay, locale)}
            >
              <Play className="h-4 w-4 fill-current" />
            </button>
            <span className="flex-1 text-sm font-semibold text-[#33492A]">
              Saved · {formatSeconds(seconds || 0)}
            </span>
            <button
              type="button"
              onClick={handleDelete}
              className="flex h-9 w-9 items-center justify-center rounded-full text-rose-500 active:bg-rose-100"
              aria-label={primary(STRINGS.delete, locale)}
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <audio
              ref={audioRef}
              src={previewUrlRef.current}
              preload="metadata"
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
              className="hidden"
            />
          </div>
        ) : null}
      </div>
      {error ? <p className={cn("mt-1.5 text-xs text-rose-600")}>{error}</p> : null}
    </div>
  );
}
