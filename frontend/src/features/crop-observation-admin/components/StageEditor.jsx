import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  createStagePractice,
  deleteStage,
  listStagePractices,
  upsertStageTranslation,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import PracticeEditor from "./PracticeEditor";
import TranslationFields from "./TranslationFields";

export default function StageEditor({ stage, practiceTemplates, onDeleted, readOnly }) {
  const [expanded, setExpanded] = useState(false);
  const [practices, setPractices] = useState([]);
  const [newPracticeCode, setNewPracticeCode] = useState(practiceTemplates[0]?.practice_code || "");

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
            labelKey="display_name"
            extraFields={["instruction_text"]}
            onSave={(locale, values) =>
              upsertStageTranslation(stage.stage_id, locale, {
                display_name: values.display_name || stage.stage_code,
                instruction_text: values.instruction_text || null,
              })
            }
          />

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
