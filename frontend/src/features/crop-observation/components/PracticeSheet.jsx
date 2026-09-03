import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  getPracticeHistory,
  savePracticeObservation,
  uploadMedia,
} from "@/features/crop-observation/api/cropObservationApi";
import PhotoPicker from "@/features/crop-observation/components/PhotoPicker";
import PreviousEntryRow from "@/features/crop-observation/components/PreviousEntryRow";
import VoiceRecorder from "@/features/crop-observation/components/VoiceRecorder";
import { STRINGS, primary } from "@/features/crop-observation/i18n";
import DynamicField from "./DynamicField";

function newClientEntryId() {
  return crypto.randomUUID ? crypto.randomUUID() : `client-${Date.now()}-${Math.random()}`;
}

export default function PracticeSheet({
  practice,
  cropCycleId,
  stageCode,
  locale,
  initialAnswers,
  onClose,
  onSaved,
}) {
  const [answers, setAnswers] = useState(initialAnswers || {});
  const [photos, setPhotos] = useState([]);
  const [voiceFile, setVoiceFile] = useState(null);
  const [voiceSeconds, setVoiceSeconds] = useState(0);
  const [saving, setSaving] = useState(false);
  const [uploadStage, setUploadStage] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");

  const [history, setHistory] = useState(null);
  const [historyError, setHistoryError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getPracticeHistory(cropCycleId, stageCode, practice.practice_code, locale, { limit: 20 })
      .then((res) => {
        if (!cancelled) setHistory(res.items || []);
      })
      .catch((err) => {
        if (!cancelled) setHistoryError(err?.message || "");
      });
    return () => {
      cancelled = true;
    };
  }, [cropCycleId, stageCode, practice.practice_code, locale]);

  function setFieldValue(fieldCode, value) {
    setAnswers((prev) => ({ ...prev, [fieldCode]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setFormError("");
    setFieldErrors({});
    try {
      setUploadStage("");
      const saved = await savePracticeObservation(cropCycleId, stageCode, practice.practice_code, {
        client_entry_id: newClientEntryId(),
        answers,
      });

      // Media only ever uploads AFTER the observation row exists — see
      // spec "do not upload media before the observation exists".
      const ownerId = saved.practice_observation_id;
      for (const file of photos) {
        setUploadStage(primary(STRINGS.uploadingMedia, locale));
        await uploadMedia({ ownerType: "PRACTICE", ownerId, mediaType: "IMAGE", mimeType: file.type, file });
      }
      if (voiceFile) {
        setUploadStage(primary(STRINGS.uploadingMedia, locale));
        await uploadMedia({
          ownerType: "PRACTICE",
          ownerId,
          mediaType: "AUDIO",
          mimeType: voiceFile.type,
          file: voiceFile,
          durationSeconds: voiceSeconds,
        });
      }

      onSaved(saved);
    } catch (err) {
      if (Array.isArray(err?.fields) && err.fields.length) {
        setFieldErrors(Object.fromEntries(err.fields.map((f) => [f.field, f.message])));
      }
      setFormError(err?.message || "Could not save. Please try again.");
    } finally {
      setSaving(false);
      setUploadStage("");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col justify-end bg-black/40 animate-in fade-in"
      onClick={onClose}
    >
      <div
        className="flex max-h-[92vh] flex-col rounded-t-3xl bg-white pb-[env(safe-area-inset-bottom)] animate-in slide-in-from-bottom-4 duration-200"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mx-auto mt-2.5 h-1 w-10 rounded-full bg-slate-200" />
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <h2 className="text-lg font-bold text-slate-950">{practice.name}</h2>
          <button
            type="button"
            onClick={onClose}
            className="grid h-9 w-9 place-items-center rounded-full text-slate-500 hover:bg-slate-100"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
          {formError ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          ) : null}

          {/* Previous entries — compact rows directly above the fresh form, per
              the "many entries over time" history model (one row per date). */}
          {history === null ? (
            !historyError ? (
              <div className="space-y-2">
                <div className="h-16 animate-pulse rounded-xl bg-slate-100" />
              </div>
            ) : null
          ) : history.length > 0 ? (
            <section>
              <div className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-600">
                {primary(STRINGS.previousEntries, locale)}
              </div>
              <div className="space-y-2">
                {history.map((entry) => (
                  <PreviousEntryRow key={entry.practice_observation_id} entry={entry} locale={locale} />
                ))}
              </div>
              <div className="my-4 border-t border-dashed border-slate-200" />
              <div className="mb-2 text-sm font-bold uppercase tracking-wide text-emerald-700">
                {primary(STRINGS.newUpdate, locale)}
              </div>
            </section>
          ) : null}

          {practice.fields.map((field) => (
            <div key={field.field_code}>
              <label className="mb-2 block text-base font-bold text-slate-900">
                {field.label}
                {field.is_required ? <span className="text-rose-600"> *</span> : null}
              </label>
              <DynamicField
                field={field}
                value={answers[field.field_code]}
                onChange={(value) => setFieldValue(field.field_code, value)}
                locale={locale}
              />
              {fieldErrors[field.field_code] ? (
                <p className="mt-1 text-xs text-rose-600">{fieldErrors[field.field_code]}</p>
              ) : null}
            </div>
          ))}

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
        </div>

        <div className="sticky bottom-0 border-t border-slate-100 bg-white px-4 py-3">
          {uploadStage ? <p className="mb-2 text-center text-xs text-slate-500">{uploadStage}</p> : null}
          <Button className="h-12 w-full rounded-xl text-base font-bold" onClick={handleSave} disabled={saving}>
            {saving ? primary(STRINGS.saving, locale) : primary(STRINGS.save, locale)}
          </Button>
        </div>
      </div>
    </div>
  );
}
