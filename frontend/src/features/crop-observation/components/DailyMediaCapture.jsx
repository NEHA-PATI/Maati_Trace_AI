import { useState } from "react";
import { Check, Loader2 } from "lucide-react";

import { uploadMedia } from "@/features/crop-observation/api/cropObservationApi";
import PhotoPicker from "@/features/crop-observation/components/PhotoPicker";
import VoiceRecorder from "@/features/crop-observation/components/VoiceRecorder";
import { STRINGS, primary } from "@/features/crop-observation/i18n";

/**
 * Photo/voice capture for the stage's main daily entry (crop status) — same
 * PhotoPicker/VoiceRecorder already used inside each practice, attached to
 * the DAILY_STAGE observation instead of a PRACTICE one. Only enabled once
 * today's status has actually been saved (auto-saves the moment a status is
 * tapped — see useCropScreen.setStatus), matching "Crop Status first".
 */
export default function DailyMediaCapture({ dailyObservationId, locale }) {
  const [photos, setPhotos] = useState([]);
  const [voiceFile, setVoiceFile] = useState(null);
  const [voiceSeconds, setVoiceSeconds] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const hasPending = photos.length > 0 || Boolean(voiceFile);

  if (!dailyObservationId) return null;

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      for (const file of photos) {
        await uploadMedia({
          ownerType: "DAILY_STAGE",
          ownerId: dailyObservationId,
          mediaType: "IMAGE",
          mimeType: file.type,
          file,
        });
      }
      if (voiceFile) {
        await uploadMedia({
          ownerType: "DAILY_STAGE",
          ownerId: dailyObservationId,
          mediaType: "AUDIO",
          mimeType: voiceFile.type,
          file: voiceFile,
          durationSeconds: voiceSeconds,
        });
      }
      setPhotos([]);
      setVoiceFile(null);
      setVoiceSeconds(0);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err?.message || "Could not save. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
      <div className="grid grid-cols-2 gap-4">
        <PhotoPicker value={photos} onChange={setPhotos} locale={locale} />
        <VoiceRecorder
          value={voiceFile}
          onChange={(file, secs) => {
            setVoiceFile(file);
            setVoiceSeconds(secs || 0);
          }}
          locale={locale}
        />
      </div>

      {error ? <p className="mt-2 text-xs text-rose-600">{error}</p> : null}

      {hasPending ? (
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="mt-3 flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 text-sm font-bold text-white active:scale-[0.99] disabled:opacity-60"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {saving ? primary(STRINGS.uploadingMedia, locale) : primary(STRINGS.save, locale)}
        </button>
      ) : saved ? (
        <p className="mt-3 flex items-center gap-1.5 text-sm font-semibold text-emerald-600">
          <Check className="h-4 w-4" /> {primary(STRINGS.saved, locale)}
        </p>
      ) : null}
    </div>
  );
}
