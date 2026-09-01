import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createField,
  deleteField,
  deleteStagePractice,
  listFields,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import FieldEditor from "./FieldEditor";

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

export default function PracticeEditor({ practice, onDeleted, readOnly }) {
  const [expanded, setExpanded] = useState(false);
  const [fields, setFields] = useState([]);
  const [newFieldCode, setNewFieldCode] = useState("");
  const [newFieldType, setNewFieldType] = useState(FIELD_TYPES[0]);
  const [newFieldRequired, setNewFieldRequired] = useState(false);

  useEffect(() => {
    if (expanded) {
      listFields(practice.stage_practice_id).then(setFields).catch(() => setFields([]));
    }
  }, [expanded, practice.stage_practice_id]);

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

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50">
      <div className="flex items-center gap-2 px-3 py-2">
        <button type="button" onClick={() => setExpanded((v) => !v)} className="text-slate-400">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <span className="flex-1 text-sm font-semibold text-slate-800">{practice.practice_code}</span>
        {!readOnly ? (
          <button type="button" onClick={handleDeletePractice} className="text-slate-400 hover:text-rose-600">
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {expanded ? (
        <div className="space-y-2 border-t border-slate-200 px-3 py-3">
          {fields.map((field) => (
            <FieldEditor key={field.field_definition_id} field={field} onDelete={handleDeleteField} readOnly={readOnly} />
          ))}

          {!readOnly ? (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dashed border-slate-300 p-2">
              <Input
                placeholder="field_code"
                value={newFieldCode}
                onChange={(e) => setNewFieldCode(e.target.value)}
                className="h-8 w-40 text-sm"
              />
              <select
                value={newFieldType}
                onChange={(e) => setNewFieldType(e.target.value)}
                className="h-8 rounded-md border border-slate-200 px-2 text-sm"
              >
                {FIELD_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <label className="flex items-center gap-1 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={newFieldRequired}
                  onChange={(e) => setNewFieldRequired(e.target.checked)}
                />
                required
              </label>
              <Button size="sm" onClick={handleAddField}>
                Add field
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
