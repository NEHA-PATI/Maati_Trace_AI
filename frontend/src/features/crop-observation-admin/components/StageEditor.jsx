import { useState } from "react";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createStagePractice,
  deleteStage,
  listStagePractices,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import InstructionAudio from "./InstructionAudio";
import PracticeEditor from "./PracticeEditor";
import SystemMediaField from "./SystemMediaField";

/**
 * One stage = one card. Shows: farmer guide (name/description per locale),
 * stage image, practices (as sub-cards), instruction audio (EN + Odia).
 * When readOnly (live view), everything renders without edit controls.
 */
export default function StageEditor({ stage, practiceTemplates, workflow, readOnly = false }) {
  const [open, setOpen] = useState(false);
  const [practices, setPractices] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newPracticeCode, setNewPracticeCode] = useState(practiceTemplates[0]?.practice_code || "");
  const [busy, setBusy] = useState(false);

  const initialEn = stage.translations?.find((t) => t.locale === "en-IN") || {};
  const initialOr = stage.translations?.find((t) => t.locale === "or-IN") || {};

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !loaded) {
      setPractices(await listStagePractices(stage.stage_id).catch(() => []));
      setLoaded(true);
    }
  }

  async function handleAddPractice() {
    if (!newPracticeCode) return;
    setBusy(true);
    try {
      await workflow?.ensureEditable();
      const created = await createStagePractice(stage.stage_id, {
        practice_code: newPracticeCode,
        display_order: practices.length,
      });
      setPractices((prev) => [...prev, created]);
      setShowAdd(false);
      await workflow?.changed();
    } finally {
      setBusy(false);
    }
  }

  function handlePracticeDeleted(id) {
    setPractices((prev) => prev.filter((p) => p.stage_practice_id !== id));
    workflow?.changed();
  }

  async function handleDeleteStage() {
    setBusy(true);
    try {
      await deleteStage(stage.stage_id);
      await workflow?.changed();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 px-4 py-3">
        <button type="button" onClick={toggle} className="flex min-w-0 flex-1 items-center gap-2 text-left">
          {open ? <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" /> : <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />}
          <span className="min-w-0 flex-1 truncate font-bold text-slate-950">
            {initialEn.display_name || stage.stage_code}
          </span>
          {stage.is_initial ? (
            <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">First</span>
          ) : null}
        </button>
        {!readOnly ? (
          <button
            type="button"
            onClick={handleDeleteStage}
            disabled={busy}
            className="shrink-0 text-slate-300 hover:text-rose-600"
            aria-label="Delete stage"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {open ? (
        <div className="space-y-4 border-t border-slate-100 p-4">
          <GuideBlock stage={stage} workflow={workflow} readOnly={readOnly} />

          <SystemMediaField
            targetType="STAGE"
            targetId={stage.stage_id}
            assetRole="STAGE_IMAGE"
            label="Stage image"
            accept="image/jpeg,image/png,image/webp"
            readOnly={readOnly}
          />

          <div className="space-y-2">
            <p className="text-xs font-bold text-slate-600">Practices</p>
            {loaded && practices.length === 0 ? (
              <p className="rounded-xl bg-slate-50 p-3 text-xs text-slate-400">No practices yet.</p>
            ) : null}
            {practices.map((practice) => (
              <PracticeEditor key={practice.stage_practice_id} practice={practice} onDeleted={handlePracticeDeleted} workflow={workflow} />
            ))}

            {!readOnly ? (
              showAdd ? (
                <div className="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 p-2">
                  <select
                    value={newPracticeCode}
                    onChange={(e) => setNewPracticeCode(e.target.value)}
                    className="h-8 flex-1 rounded-md border border-slate-200 px-2 text-sm"
                  >
                    {practiceTemplates.map((t) => (
                      <option key={t.practice_code} value={t.practice_code}>
                        {(t.translations?.find((x) => x.locale === "en-IN")?.display_name) || t.practice_code}
                      </option>
                    ))}
                  </select>
                  <Button size="sm" onClick={handleAddPractice} disabled={busy}>Add</Button>
                  <Button size="sm" variant="outline" onClick={() => setShowAdd(false)}>Cancel</Button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowAdd(true)}
                  className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  + Add practice
                </button>
              )
            ) : null}
          </div>

          <InstructionAudio stage={stage} workflow={workflow} readOnly={readOnly} />
        </div>
      ) : null}
    </div>
  );
}

/** Farmer guide: EN + Odia name and description, saved via stage translation. */
function GuideBlock({ stage, workflow, readOnly }) {
  const initialEn = stage.translations?.find((t) => t.locale === "en-IN") || {};
  const initialOr = stage.translations?.find((t) => t.locale === "or-IN") || {};
  const [values, setValues] = useState({
    "en-IN": initialEn.display_name || "",
    "or-IN": initialOr.display_name || "",
    "en-IN-desc": initialEn.short_description || "",
    "or-IN-desc": initialOr.short_description || "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save() {
    setSaving(true);
    try {
      const { upsertStageTranslation } = await import("@/features/crop-observation-admin/api/cropObservationAdminApi");
      await Promise.all([
        upsertStageTranslation(stage.stage_id, "en-IN", {
          display_name: values["en-IN"] || stage.stage_code,
          instruction_text: initialEn.instruction_text ?? null,
          short_description: values["en-IN-desc"] || null,
        }),
        upsertStageTranslation(stage.stage_id, "or-IN", {
          display_name: values["or-IN"] || stage.stage_code,
          instruction_text: initialOr.instruction_text ?? null,
          short_description: values["or-IN-desc"] || null,
        }),
      ]);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      await workflow?.changed();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-slate-600">Farmer guide</p>
        {!readOnly ? (
          <Button size="sm" variant="outline" onClick={save} disabled={saving}>
            {saving ? "Saving…" : saved ? "✓ Saved" : "Save"}
          </Button>
        ) : null}
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        {[
          { key: "en-IN", label: "English name" },
          { key: "or-IN", label: "ଓଡ଼ିଆ name" },
          { key: "en-IN-desc", label: "English description" },
          { key: "or-IN-desc", label: "ଓଡ଼ିଆ description" },
        ].map(({ key, label }) => (
          <label key={key} className="block">
            <span className="text-[11px] font-semibold text-slate-500">{label}</span>
            <Input
              className="mt-0.5 h-8 text-sm"
              value={values[key]}
              disabled={readOnly}
              onChange={(e) => setValues((p) => ({ ...p, [key]: e.target.value }))}
            />
          </label>
        ))}
      </div>
    </div>
  );
}
