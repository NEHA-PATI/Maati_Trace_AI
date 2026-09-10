import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createField,
  deleteField,
  deleteStagePractice,
  listFields,
  updateStagePractice,
  upsertPracticeTranslation,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import FieldEditor from "./FieldEditor";
import SystemMediaField from "./SystemMediaField";
import TranslationFields from "./TranslationFields";

const FIELD_TYPES = [
  "SINGLE_CHOICE",
  "MULTI_CHOICE",
  "PICTURE_CHOICE",
  "YES_NO_UNKNOWN",
  "SEVERITY",
  "QUANTITY_UNIT",
  "NUMBER",
  "SHORT_TEXT",
  "BOOLEAN",
  "PRODUCT",
  "PEST",
  "DISEASE",
  "APPLICATION_AREA",
];

const DEFAULT_MEDIA = {
  issue_evidence: { enabled: false, max_images: 2, required: false },
  practice_evidence: { enabled: true, max_images: 2, required: false },
  voice_note: { enabled: true, max_count: 1, max_seconds: 60 },
};

function normalizeMediaConfig(input) {
  return {
    issue_evidence: { ...DEFAULT_MEDIA.issue_evidence, ...(input?.issue_evidence || {}) },
    practice_evidence: { ...DEFAULT_MEDIA.practice_evidence, ...(input?.practice_evidence || {}) },
    voice_note: { ...DEFAULT_MEDIA.voice_note, ...(input?.voice_note || {}) },
  };
}

export default function PracticeEditor({ practice, onDeleted, readOnly }) {
  const [expanded, setExpanded] = useState(false);
  const [fields, setFields] = useState([]);
  const [newFieldCode, setNewFieldCode] = useState("");
  const [newFieldType, setNewFieldType] = useState(FIELD_TYPES[0]);
  const [newFieldRequired, setNewFieldRequired] = useState(false);
  const [mediaConfig, setMediaConfig] = useState(() => normalizeMediaConfig(practice.media_config));
  const [mediaConfigStatus, setMediaConfigStatus] = useState("");

  useEffect(() => {
    setMediaConfig(normalizeMediaConfig(practice.media_config));
  }, [practice.media_config]);

  useEffect(() => {
    if (expanded) {
      listFields(practice.stage_practice_id).then(setFields).catch(() => setFields([]));
    }
  }, [expanded, practice.stage_practice_id]);

  const summary = useMemo(() => {
    const parts = [];
    if (mediaConfig.issue_evidence.enabled) parts.push(`${mediaConfig.issue_evidence.max_images} issue photos`);
    if (mediaConfig.practice_evidence.enabled) parts.push(`${mediaConfig.practice_evidence.max_images} action photos`);
    if (mediaConfig.voice_note.enabled) parts.push(`${mediaConfig.voice_note.max_seconds}s voice`);
    return parts.join(" · ") || "No farmer media";
  }, [mediaConfig]);

  async function handleAddField() {
    if (!newFieldCode.trim()) return;
    const created = await createField(practice.stage_practice_id, {
      field_code: newFieldCode.trim(),
      field_type: newFieldType,
      display_order: fields.length,
      is_required: newFieldRequired,
    });
    setFields((prev) => [...prev, created]);
    setNewFieldCode("");
    setNewFieldRequired(false);
  }

  async function handleDeleteField(fieldId) {
    await deleteField(fieldId);
    setFields((prev) => prev.filter((f) => f.field_definition_id !== fieldId));
  }

  async function handleDeletePractice() {
    await deleteStagePractice(practice.stage_practice_id);
    onDeleted(practice.stage_practice_id);
  }

  function patch(section, values) {
    setMediaConfig((prev) => ({ ...prev, [section]: { ...prev[section], ...values } }));
  }

  async function handleSaveMediaConfig() {
    setMediaConfigStatus("");
    try {
      await updateStagePractice(practice.stage_practice_id, { media_config: mediaConfig });
      setMediaConfigStatus("Saved");
    } catch (error) {
      setMediaConfigStatus(error?.message || "Could not save media policy");
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50">
      <div className="flex items-center gap-2 px-3 py-2">
        <button type="button" onClick={() => setExpanded((v) => !v)} className="text-slate-400">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <div className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold text-slate-800">{practice.practice_code}</span>
          <span className="block truncate text-[11px] text-slate-400">{summary}</span>
        </div>
        {!readOnly ? (
          <button type="button" onClick={handleDeletePractice} className="text-slate-400 hover:text-rose-600">
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {expanded ? (
        <div className="space-y-3 border-t border-slate-200 px-3 py-3">
          <TranslationFields
            initialEn={practice.translations?.find((item) => item.locale === "en-IN") || {}}
            initialOr={practice.translations?.find((item) => item.locale === "or-IN") || {}}
            labelKey="display_name"
            extraFields={["help_text"]}
            onSave={(locale, values) => upsertPracticeTranslation(practice.practice_template_id, locale, {
              display_name: values.display_name || practice.practice_code,
              help_text: values.help_text || null,
            })}
          />
          <SystemMediaField
            targetType="STAGE_PRACTICE"
            targetId={practice.stage_practice_id}
            assetRole="PRACTICE_GUIDE_IMAGE"
            label="Practice guide image (optional)"
            accept="image/jpeg,image/png,image/webp"
            readOnly={readOnly}
            compact
          />

          <div className="rounded-xl border border-emerald-100 bg-white p-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Farmer evidence</p>
                <p className="mt-1 text-xs text-slate-400">Configure the capture controls shown for this practice. No JSON editing required.</p>
              </div>
              {!readOnly ? <Button size="sm" variant="outline" onClick={handleSaveMediaConfig}>Save evidence settings</Button> : null}
            </div>

            <div className="mt-3 grid gap-3 lg:grid-cols-3">
              <MediaRuleCard
                title="Problem / issue photos"
                enabled={mediaConfig.issue_evidence.enabled}
                max={mediaConfig.issue_evidence.max_images}
                maxLimit={2}
                readOnly={readOnly}
                onEnabled={(enabled) => patch("issue_evidence", { enabled })}
                onMax={(max_images) => patch("issue_evidence", { max_images })}
              />
              <MediaRuleCard
                title="Practice / action photos"
                enabled={mediaConfig.practice_evidence.enabled}
                max={mediaConfig.practice_evidence.max_images}
                maxLimit={2}
                readOnly={readOnly}
                onEnabled={(enabled) => patch("practice_evidence", { enabled })}
                onMax={(max_images) => patch("practice_evidence", { max_images })}
              />
              <div className="rounded-lg border bg-slate-50 p-3">
                <label className="flex items-center gap-2 text-sm font-bold text-slate-800">
                  <input type="checkbox" disabled={readOnly} checked={mediaConfig.voice_note.enabled} onChange={(e) => patch("voice_note", { enabled: e.target.checked })} />
                  Farmer voice note
                </label>
                <label className="mt-3 block text-xs font-semibold text-slate-500">Maximum seconds</label>
                <input type="number" min="5" max="60" disabled={readOnly || !mediaConfig.voice_note.enabled} value={mediaConfig.voice_note.max_seconds} onChange={(e) => patch("voice_note", { max_seconds: Math.min(60, Math.max(5, Number(e.target.value) || 60)) })} className="mt-1 h-9 w-full rounded-lg border bg-white px-2 text-sm" />
                <p className="mt-2 text-[11px] text-slate-400">One voice note per record.</p>
              </div>
            </div>
            {mediaConfigStatus ? <p className="mt-2 text-xs font-semibold text-emerald-700">{mediaConfigStatus}</p> : null}
          </div>

          {fields.map((field) => (
            <FieldEditor key={field.field_definition_id} field={field} onDelete={handleDeleteField} readOnly={readOnly} />
          ))}

          {!readOnly ? (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dashed border-slate-300 p-2">
              <Input placeholder="field_code" value={newFieldCode} onChange={(e) => setNewFieldCode(e.target.value)} className="h-8 w-40 text-sm" />
              <select value={newFieldType} onChange={(e) => setNewFieldType(e.target.value)} className="h-8 rounded-md border border-slate-200 px-2 text-sm">
                {FIELD_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <label className="flex items-center gap-1 text-xs text-slate-600"><input type="checkbox" checked={newFieldRequired} onChange={(e) => setNewFieldRequired(e.target.checked)} />required</label>
              <Button size="sm" onClick={handleAddField}>Add field</Button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function MediaRuleCard({ title, enabled, max, maxLimit, readOnly, onEnabled, onMax }) {
  return (
    <div className="rounded-lg border bg-slate-50 p-3">
      <label className="flex items-center gap-2 text-sm font-bold text-slate-800"><input type="checkbox" disabled={readOnly} checked={enabled} onChange={(e) => onEnabled(e.target.checked)} />{title}</label>
      <label className="mt-3 block text-xs font-semibold text-slate-500">Maximum images</label>
      <select disabled={readOnly || !enabled} value={max} onChange={(e) => onMax(Number(e.target.value))} className="mt-1 h-9 w-full rounded-lg border bg-white px-2 text-sm">
        {Array.from({ length: maxLimit }, (_, i) => i + 1).map((n) => <option key={n} value={n}>{n}</option>)}
      </select>
    </div>
  );
}
