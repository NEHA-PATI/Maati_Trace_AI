import { useEffect, useState } from "react";
import { Check, Loader2, Play } from "lucide-react";

import {
  fetchTtsVoicePreview,
  listTtsVoices,
  resolveCropObservationServiceUrl,
  upsertTtsProfile,
} from "../api/cropObservationAdminApi";

/**
 * Voice selector with preview playback. Replaces the raw "paste your
 * Cartesia Voice ID" input — the admin picks a voice by listening to it.
 * Voice profiles are global (one EN, one Odia) and applied at generation
 * time; already-generated clips stay until regenerated.
 */
export default function VoicePicker({ locale, profile, onSaved }) {
  const [voices, setVoices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [playingId, setPlayingId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setVoices(await listTtsVoices(locale));
    } catch (err) {
      setError(err?.message || "Could not load voices.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function play(voiceId) {
    setPlayingId(voiceId);
    try {
      const blob = await fetchTtsVoicePreview(voiceId);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        setPlayingId("");
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch {
      setPlayingId("");
    }
  }

  async function save(voiceId) {
    if (!voiceId || busy) return;
    setBusy(true);
    setError("");
    try {
      const selected = voices.find((v) => v.voice_id === voiceId);
      await upsertTtsProfile(locale, { voice_id: voiceId, voice_name: selected?.name || null });
      await onSaved?.();
    } catch (err) {
      setError(err?.message || "Could not save voice.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-slate-600">
          {locale === "or-IN" ? "ଓଡ଼ିଆ (Odia) voice" : "English voice"}
        </label>
        <button type="button" onClick={load} disabled={loading} className="text-[11px] font-semibold text-emerald-700 hover:underline">
          {loading ? "loading…" : "refresh"}
        </button>
      </div>

      {voices.length ? (
        <div className="max-h-44 space-y-1 overflow-y-auto rounded-lg border border-slate-200 bg-white p-1">
          {voices.map((v) => (
            <button
              key={v.voice_id}
              type="button"
              disabled={busy}
              onClick={() => save(v.voice_id)}
              className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition ${profile?.voice_id === v.voice_id ? "bg-emerald-50 ring-1 ring-emerald-300" : "hover:bg-slate-50"
                }`}
            >
              {profile?.voice_id === v.voice_id ? (
                <Check className="h-3.5 w-3.5 shrink-0 text-emerald-700" />
              ) : (
                <span className="h-3.5 w-3.5 shrink-0" />
              )}
              <span className="min-w-0 flex-1 truncate font-medium text-slate-700">{v.name}</span>
              {v.preview_url ? (
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => { e.stopPropagation(); play(v.voice_id); }}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); play(v.voice_id); } }}
                  className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-100 hover:bg-emerald-100"
                >
                  {playingId === v.voice_id ? <Loader2 className="h-3 w-3 animate-spin text-emerald-700" /> : <Play className="h-3 w-3 text-emerald-700" />}
                </span>
              ) : null}
            </button>
          ))}
        </div>
      ) : (
        <p className="rounded-lg bg-slate-50 p-2 text-xs text-slate-500">
          {loading ? "Loading voices from Cartesia…" : "No voices loaded yet."}
        </p>
      )}

      {profile?.voice_name ? (
        <p className="text-[11px] text-slate-400">Current: {profile.voice_name}</p>
      ) : null}
      {error ? <p className="text-[11px] font-medium text-rose-600">{error}</p> : null}
    </div>
  );
}
