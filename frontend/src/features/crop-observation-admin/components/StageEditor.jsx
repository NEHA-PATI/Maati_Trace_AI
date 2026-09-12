import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  createStagePractice,
  deleteStage,
  generateStageInstructionAudio,
  listStagePractices,
  upsertStageTranslation,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import PracticeEditor from "./PracticeEditor";
import TranslationFields from "./TranslationFields";
import SystemMediaField from "./SystemMediaField";

export default function StageEditor({ stage, practiceTemplates, onDeleted, readOnly }) {
  const initialEn = stage.translations?.find((item) => item.locale === "en-IN") || {};
  const initialOr = stage.translations?.find((item) => item.locale === "or-IN") || {};
  const [expanded, setExpanded] = useState(false);
  const [practices, setPractices] = useState([]);
  const [newPracticeCode, setNewPracticeCode] = useState(practiceTemplates[0]?.practice_code || "");
  const [audioBusy, setAudioBusy] = useState("");
  const [audioStatus, setAudioStatus] = useState("");
  const [instructionText, setInstructionText] = useState({
    "en-IN": initialEn.instruction_text || "",
    "or-IN": initialOr.instruction_text || "",
  });

  useEffect(() => {
    if (expanded) {
      listStagePractices(stage.stage_id).then(setPractices).catch(() => setPractices([]));
    }
  }, [expanded, stage.stage_id]);

  async function handleAddPractice() {
    if (!newPracticeCode) return;
    const created = await createStagePractice(stage.stage_id, {
      practice_code: newPracticeCode,
      display_order: practices.length,
    });
    setPractices((prev) => [...prev, created]);
  }

  async function handleDeletePractice(id) {
    setPractices((prev) => prev.filter((p) => p.stage_practice_id !== id));
  }

  async function handleDeleteStage() {
    await deleteStage(stage.stage_id);
    onDeleted(stage.stage_id);
  }

  async function handleGenerateAudio(locale) {
    setAudioBusy(locale);
    setAudioStatus("");
    try {
      await generateStageInstructionAudio(stage.stage_id, locale, { force: false });
      setAudioStatus(`Generated ${locale}`);
    } catch (error) {
      setAudioStatus(error?.message || "Could not generate audio.");
    } finally {
      setAudioBusy("");
    }
  }

  async function handleSaveInstructionText(locale) {
    setAudioStatus("");
    try {
      await upsertStageTranslation(stage.stage_id, locale, {
        display_name: (locale === "en-IN" ? initialEn.display_name : initialOr.display_name) || stage.stage_code,
        instruction_text: instructionText[locale].trim() || null,
      });
      setAudioStatus(`Saved ${locale} instruction text`);
    } catch (error) {
      setAudioStatus(error?.message || "Could not save instruction text.");
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 px-4 py-3">
        <button type="button" onClick={() => setExpanded((v) => !v)} className="text-slate-400">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <span className="flex-1 font-semibold text-slate-900">
          {stage.stage_code}
          {stage.is_initial ? <span className="ml-2 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">initial</span> : null}
        </span>
        {!readOnly ? (
          <button type="button" onClick={handleDeleteStage} className="text-slate-400 hover:text-rose-600">
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {expanded ? (
        <div className="space-y-4 border-t border-slate-100 px-4 py-4">
          <TranslationFields
            initialEn={initialEn}
            initialOr={initialOr}
            labelKey="display_name"
            extraFields={["short_description"]}
            onSave={(locale, values) =>
              upsertStageTranslation(stage.stage_id, locale, {
                display_name: values.display_name || stage.stage_code,
                instruction_text: values.instruction_text || null,
              })
            }
          />

          <div className="grid gap-3 lg:grid-cols-2">
            <SystemMediaField
              targetType="STAGE"
              targetId={stage.stage_id}
              assetRole="STAGE_IMAGE"
              label="Stage image"
              accept="image/jpeg,image/png,image/webp"
              readOnly={readOnly}
            />
            <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Instruction audio</p>
              <p className="mt-1 text-xs text-slate-500">Enter speech text in both languages, save it, then generate with Cartesia or replace it with your own recording.</p>
              <div className="mt-3 grid gap-3 lg:grid-cols-2">
                {[{ locale: "en-IN", label: "English" }, { locale: "or-IN", label: "ଓଡ଼ିଆ (Odia)" }].map(({ locale, label }) => (
                  <div key={locale} className="rounded-lg border border-emerald-100 bg-white p-2">
                    <label className="block text-xs font-bold text-slate-600">{label} speech text</label>
                    <textarea
                      value={instructionText[locale]}
                      onChange={(event) => setInstructionText((previous) => ({ ...previous, [locale]: event.target.value }))}
                      maxLength={1200}
                      rows={3}
                      placeholder={`Type the ${label} instruction…`}
                      className="mt-1 w-full rounded-md border px-2 py-1.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    {!readOnly ? <Button size="sm" variant="outline" onClick={() => handleSaveInstructionText(locale)}>Save text</Button> : null}
                  </div>
                ))}
              </div>
              <div className="mt-3 grid gap-2">
                <div className="grid gap-2 sm:grid-cols-[1fr_auto] sm:items-center">
                  <SystemMediaField
                    targetType="STAGE"
                    targetId={stage.stage_id}
                    assetRole="INSTRUCTION_AUDIO"
                    locale="en-IN"
                    label="English instruction"
                    accept="audio/mpeg,audio/wav,audio/ogg,audio/mp4"
                    readOnly={readOnly}
                    compact
                    key={`en-${audioStatus}`}
                  />
                  {!readOnly ? <Button size="sm" variant="outline" disabled={audioBusy === "en-IN"} onClick={() => handleGenerateAudio("en-IN")}>{audioBusy === "en-IN" ? "Generating…" : "Generate"}</Button> : null}
                </div>
                <div className="grid gap-2 sm:grid-cols-[1fr_auto] sm:items-center">
                  <SystemMediaField
                    targetType="STAGE"
                    targetId={stage.stage_id}
                    assetRole="INSTRUCTION_AUDIO"
                    locale="or-IN"
                    label="Odia instruction"
                    accept="audio/mpeg,audio/wav,audio/ogg,audio/mp4"
                    readOnly={readOnly}
                    compact
                    key={`or-${audioStatus}`}
                  />
                  {!readOnly ? <Button size="sm" variant="outline" disabled={audioBusy === "or-IN"} onClick={() => handleGenerateAudio("or-IN")}>{audioBusy === "or-IN" ? "Generating…" : "Generate"}</Button> : null}
                </div>
              </div>
              {audioStatus ? <p className="mt-2 text-xs text-slate-600">{audioStatus}</p> : null}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-semibold text-slate-500">Practices</p>
            <div className="space-y-2">
              {practices.map((practice) => (
                <PracticeEditor
                  key={practice.stage_practice_id}
                  practice={practice}
                  onDeleted={handleDeletePractice}
                  readOnly={readOnly}
                />
              ))}
            </div>

            {!readOnly ? (
              <div className="mt-2 flex items-center gap-2">
                <select
                  value={newPracticeCode}
                  onChange={(e) => setNewPracticeCode(e.target.value)}
                  className="h-8 rounded-md border border-slate-200 px-2 text-sm"
                >
                  {practiceTemplates.map((t) => (
                    <option key={t.practice_code} value={t.practice_code}>
                      {t.practice_code}
                    </option>
                  ))}
                </select>
                <Button size="sm" onClick={handleAddPractice}>
                  Add practice
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
