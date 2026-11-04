import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createStagePractice,
  createStagePracticeField,
  listPracticeFieldTemplates,
  updateStagePracticeField,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";

export default function StageEditor({ stage, practiceTemplates, workflow }) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showAddPractice, setShowAddPractice] = useState(false);
  const [newPracticeCode, setNewPracticeCode] = useState("");
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  async function load() {
    const fieldTemplates = await listPracticeFieldTemplates();
    setTemplates(fieldTemplates);
  }

  async function handlePickTemplate(templateId) {
    if (!templateId) return;
    const configId = await workflow.ensureEditable();
    if (!configId) return;
    await createStagePracticeField(configId, stage.stage_id, { field_template_id: templateId });
    setShowTemplates(false);
    await workflow.changed();
  }

  const guide = stage.guide || {};
  const fieldTemplates = stage.field_templates || [];
  const practices = stage.practices || [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full flex-wrap items-center justify-between gap-2 p-4 text-left"
      >
        <span className="min-w-0 truncate font-bold text-slate-950">{stage.stage_code}</span>
        <span className="inline-flex shrink-0 items-center gap-1.5 text-xs text-slate-500">
          {open ? <ChevronDown className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
          {open ? "Close" : "Pick template"}
        </span>
      </button>

      {open ? (
        <div className="space-y-4 border-t border-slate-100 p-4">
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs font-bold text-slate-600">Farmer guide</p>
            <p className="mt-1 text-sm text-slate-700">{guide.guide_text_en || "No guide yet."}</p>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 p-3">
            <Input
              placeholder="Pick template"
              value={newPracticeCode}
              onChange={(e) => setNewPracticeCode(e.target.value)}
              className="h-8 text-sm"
              onKeyDown={(e) => { if (e.key === "Enter") handlePickTemplate(templates[0]?.field_template_id); }}
            />
            <Button size="sm" onClick={() => setShowTemplates((v) => !v)}>Pick</Button>
          </div>

          {templates.map((template) => (
            <PracticeEditor key={template.field_template_id} practice={template} workflow={workflow} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
