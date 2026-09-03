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
import { iconForField } from "./fieldIcons";

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
  const [issuePhotos, setIssuePhotos] = useState([]);
  const [practicePhotos, setPracticePhotos] = useState([]);
  const [voiceFile, setVoiceFile] = useState(null);
  const [voiceSeconds, setVoiceSeconds] = useState(0);
  const [saving, setSaving] = useState(false);
  const [uploadStage, setUploadStage] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [history, setHistory] = useState(null);
  const [historyError, setHistoryError] = useState("");

  const mediaConfig = practice.media_config || {};
  const issueEnabled = mediaConfig.issue_evidence?.enabled;
  const issueMax = mediaConfig.issue_evidence?.max_images || 2;
  const practiceEnabled = mediaConfig.practice_evidence?.enabled ?? true;
  const practiceMax = mediaConfig.practice_evidence?.max_images || 2;
  const voiceEnabled = mediaConfig.voice_note?.enabled ?? true;
  const voiceMaxSeconds = mediaConfig.voice_note?.max_seconds || 60;

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

      const ownerId = saved.practice_observation_id;
      for (const file of issuePhotos) {
        setUploadStage(primary(STRINGS.uploadingMedia, locale));
        await uploadMedia({
          ownerType: "PRACTICE",
          ownerId,
          mediaType: "IMAGE",
          mediaPurpose: "ISSUE_EVIDENCE",
          mimeType: file.type,
          file,
        });
      }
      for (const file of practicePhotos) {
        setUploadStage(primary(STRINGS.uploadingMedia, locale));
        await uploadMedia({
          ownerType: "PRACTICE",
          ownerId,
          mediaType: "IMAGE",
          mediaPurpose: "PRACTICE_EVIDENCE",
          mimeType: file.type,
          file,
        });
      }
      if (voiceFile && voiceEnabled) {
        setUploadStage(primary(STRINGS.uploadingMedia, locale));
        await uploadMedia({
          ownerType: "PRACTICE",
          ownerId,
          mediaType: "AUDIO",
          mediaPurpose: "GENERAL",
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
      setFormError(
        err?.code === "STAGE_STATUS_REQUIRED"
          ? "Save today's crop status first."
          : err?.message || "Could not save. Please try again.",
      );
    } finally {
      setSaving(false);
      setUploadStage("");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/40 animate-in fade-in" onClick={onClose}>
      <div
        className="flex max-h-[88vh] flex-col rounded-t-[22px] bg-white pb-[env(safe-area-inset-bottom)] shadow-2xl animate-in slide-in-from-bottom-4 duration-200"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mx-auto mt-2.5 h-1 w-10 rounded-full bg-[#E9E7DC]" />
        <div className="flex items-center justify-between border-b border-[#E9E7DC] px-4 py-3">
          <h2 className="min-w-0 flex-1 truncate text-[17px] font-bold text-[#1D2117]">{practice.name}</h2>
          <button
            type="button"
            onClick={onClose}
            className="grid h-10 w-10 place-items-center rounded-[10px] border border-[#E9E7DC] bg-[#F7F8F3] text-[#5B6055]"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {formError ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          ) : null}

          {history === null ? (
            !historyError ? <div className="h-16 animate-pulse rounded-xl bg-[#F7F8F3]" /> : null
          ) : history.length > 0 ? (
            <section>
              <div className="mb-2 text-sm font-bold text-[#5B6055]">
                {primary(STRINGS.previousEntries, locale)}
              </div>
              <div className="space-y-2">
                {history.map((entry) => (
                  <PreviousEntryRow key={entry.practice_observation_id} entry={entry} locale={locale} />
                ))}
              </div>
              <div className="my-4 border-t border-dashed border-[#E9E7DC]" />
              <div className="mb-2 text-sm font-bold text-[#4B6B3A]">{primary(STRINGS.newUpdate, locale)}</div>
            </section>
          ) : null}

          {practice.fields.map((field) => {
            const FieldIcon = iconForField(field);
            return (
              <div key={field.field_code} className="space-y-2">
                <label className="flex items-center gap-2 text-[15px] font-bold text-[#1D2117]">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E1F1D6] text-[#33492A]">
                    <FieldIcon className="h-5 w-5" />
                  </span>
                  <span className="min-w-0 flex-1">
                    {field.label}
                    {field.is_required ? <span className="text-rose-600"> *</span> : null}
                  </span>
                </label>
                <DynamicField
                  field={field}
                  value={answers[field.field_code]}
                  onChange={(value) => setFieldValue(field.field_code, value)}
                  locale={locale}
                />
                {fieldErrors[field.field_code] ? (
                  <p className="text-xs text-rose-600">{fieldErrors[field.field_code]}</p>
                ) : null}
              </div>
            );
          })}

          <div className="space-y-4">
            {issueEnabled ? (
              <PhotoPicker
                value={issuePhotos}
                onChange={setIssuePhotos}
                locale={locale}
                title="Problem photos"
                maxImages={issueMax}
              />
            ) : null}
            {practiceEnabled ? (
              <PhotoPicker
                value={practicePhotos}
                onChange={setPracticePhotos}
                locale={locale}
                title="Action photos"
                maxImages={practiceMax}
              />
            ) : null}
            {voiceEnabled ? (
              <VoiceRecorder
                value={voiceFile}
                onChange={(file, secs) => {
                  setVoiceFile(file);
                  setVoiceSeconds(secs || 0);
                }}
                locale={locale}
                maxSeconds={voiceMaxSeconds}
              />
            ) : null}
          </div>
        </div>

        <div className="sticky bottom-0 border-t border-[#E9E7DC] bg-white px-4 py-3">
          {uploadStage ? <p className="mb-2 text-center text-xs text-[#5B6055]">{uploadStage}</p> : null}
          <Button className="h-[52px] w-full rounded-[14px] bg-[#4B6B3A] text-base font-bold hover:bg-[#33492A]" onClick={handleSave} disabled={saving}>
            {saving ? primary(STRINGS.saving, locale) : primary(STRINGS.save, locale)}
          </Button>
        </div>
      </div>
    </div>
  );
}
