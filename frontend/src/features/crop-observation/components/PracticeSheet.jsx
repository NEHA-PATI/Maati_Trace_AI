import { useState } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { savePracticeObservation } from "@/features/crop-observation/api/cropObservationApi";
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
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");

  function setFieldValue(fieldCode, value) {
    setAnswers((prev) => ({ ...prev, [fieldCode]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setFormError("");
    setFieldErrors({});
    try {
      const saved = await savePracticeObservation(cropCycleId, stageCode, practice.practice_code, {
        client_entry_id: newClientEntryId(),
        answers,
      });
      onSaved(saved);
    } catch (err) {
      if (Array.isArray(err?.fields) && err.fields.length) {
        setFieldErrors(Object.fromEntries(err.fields.map((f) => [f.field, f.message])));
      }
      setFormError(err?.message || "Could not save. Please try again.");
    } finally {
      setSaving(false);
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

          {practice.fields.map((field) => (
            <div key={field.field_code}>
              <label className="mb-2 block text-sm font-semibold text-slate-800">
                {field.label}
                {field.is_required ? <span className="text-rose-500"> *</span> : null}
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
        </div>

        <div className="sticky bottom-0 border-t border-slate-100 bg-white px-4 py-3">
          <Button className="h-12 w-full rounded-xl text-base font-bold" onClick={handleSave} disabled={saving}>
            {saving ? primary(STRINGS.saving, locale) : primary(STRINGS.save, locale)}
          </Button>
        </div>
      </div>
    </div>
  );
}
