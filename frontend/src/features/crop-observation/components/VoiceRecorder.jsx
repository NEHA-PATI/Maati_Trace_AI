import { useEffect, useRef, useState } from "react";
import { Mic, Play, Square, Trash2 } from "lucide-react";

import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const MAX_SECONDS = 60;
// Safari/iOS don't support audio/webm; MediaRecorder.isTypeSupported picks
// whichever the device actually has. The backend already accepts all of
// webm/ogg/mp4/mpeg/wav (see ALLOWED_AUDIO_MIME_TYPES).
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

/**
 * One farmer voice note, max 60 seconds — navigator.mediaDevices +
 * MediaRecorder only, no server speech engine, no upload API here (the
 * parent uploads `value` after the observation itself is saved).
 */
export default function VoiceRecorder({ value, onChange, locale }) {
  const [status, setStatus] = useState(value ? "recorded" : "idle"); // idle | requesting | recording | recorded
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const previewUrlRef = useRef(null);

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
        onChange(file, seconds);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setStatus("recording");
      setSeconds(0);
      timerRef.current = window.setInterval(() => {
        setSeconds((prev) => {
          const next = prev + 1;
          if (next >= MAX_SECONDS) stopRecording();
          return next;
        });
      }, 1000);
    } catch {
      setStatus("idle");
      setError(
        locale === "or-IN"
          ? "ମାଇକ୍ରୋଫୋନ୍ ବ୍ୟବହାର କରିପାରିଲା ନାହିଁ।"
          : "Could not access the microphone.",
      );
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
  }

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
    } else {
      audio.currentTime = 0;
      audio.play();
    }
  }

  return (
    <div>
      <div className="text-base font-bold text-slate-900">{primary(STRINGS.recordVoice, locale)}</div>
      <div className="mt-2">
        {status === "idle" || status === "requesting" ? (
          <button
            type="button"
            onClick={startRecording}
            disabled={status === "requesting"}
            className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-500 text-white shadow-md shadow-rose-200 transition active:scale-95 disabled:opacity-60"
            aria-label={primary(STRINGS.recordVoice, locale)}
          >
            <Mic className="h-6 w-6" />
          </button>
        ) : null}

        {status === "recording" ? (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={stopRecording}
              className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-600 text-white shadow-md shadow-rose-200"
              aria-label={primary(STRINGS.stopRecording, locale)}
            >
              <Square className="h-5 w-5 fill-current" />
            </button>
            <div className="flex items-center gap-2 text-rose-600">
              <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-rose-500" />
              <span className="text-sm font-bold tabular-nums">{formatSeconds(seconds)} / 1:00</span>
            </div>
          </div>
        ) : null}

        {status === "recorded" && value ? (
          <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2">
            <button
              type="button"
              onClick={togglePlay}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white"
              aria-label={primary(STRINGS.replay, locale)}
            >
              <Play className="h-4 w-4 fill-current" />
            </button>
            <span className="flex-1 text-sm font-semibold text-emerald-700">
              🎤 {formatSeconds(seconds || 0)}
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
