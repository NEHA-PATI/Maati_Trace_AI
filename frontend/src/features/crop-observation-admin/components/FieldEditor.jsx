import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createOption,
  deleteOption,
  listOptions,
  upsertFieldTranslation,
  upsertOptionTranslation,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import TranslationFields from "./TranslationFields";
import SystemMediaField from "./SystemMediaField";

const CHOICE_TYPES = new Set(["SINGLE_CHOICE", "MULTI_CHOICE", "PICTURE_CHOICE", "PRODUCT", "PEST", "DISEASE"]);

export default function FieldEditor({ field, onDelete, readOnly }) {
  const [expanded, setExpanded] = useState(false);
  const [options, setOptions] = useState([]);
  const [newOptionCode, setNewOptionCode] = useState("");
  const needsOptions = CHOICE_TYPES.has(field.field_type);
  const initialEn = field.translations?.find((item) => item.locale === "en-IN") || {};
  const initialOr = field.translations?.find((item) => item.locale === "or-IN") || {};

  useEffect(() => {
    if (expanded && needsOptions) {
      listOptions(field.field_definition_id).then(setOptions).catch(() => setOptions([]));
    }
  }, [expanded, needsOptions, field.field_definition_id]);

  async function handleAddOption() {
    if (!newOptionCode.trim()) return;
    const created = await createOption(field.field_definition_id, {
      option_code: newOptionCode.trim().toUpperCase().replace(/\s+/g, "_"),
      display_order: options.length,
    });
    setOptions((prev) => [...prev, created]);
    setNewOptionCode("");
  }

  async function handleDeleteOption(optionId) {
    await deleteOption(optionId);
    setOptions((prev) => prev.filter((o) => o.field_option_id !== optionId));
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center gap-2 px-3 py-2">
        <button type="button" onClick={() => setExpanded((v) => !v)} className="text-slate-400">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <span className="flex-1 text-sm font-medium text-slate-800">
          {field.field_code} <span className="text-xs text-slate-400">({field.field_type})</span>
          {field.is_required ? <span className="ml-1 text-xs text-rose-500">required</span> : null}
        </span>
        {!readOnly ? (
          <button
            type="button"
            onClick={() => onDelete(field.field_definition_id)}
            className="text-slate-400 hover:text-rose-600"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {expanded ? (
        <div className="space-y-3 border-t border-slate-100 px-3 py-3">
          <TranslationFields
            initialEn={initialEn}
            initialOr={initialOr}
            labelKey="label"
            extraFields={["help_text"]}
            onSave={(locale, values) =>
              upsertFieldTranslation(field.field_definition_id, locale, {
                label: values.label || field.field_code,
                help_text: values.help_text || null,
              })
            }
          />

          {needsOptions ? (
            <div>
              <p className="mb-1 text-xs font-semibold text-slate-500">Options</p>
              <div className="space-y-1">
                {options.map((option) => (
                  <div key={option.field_option_id} className="rounded-lg border border-slate-100 bg-slate-50 p-2">
                    <div className="flex items-center gap-2">
                      <span className="min-w-0 flex-1 truncate text-sm font-semibold">{option.option_code}</span>
                      <TranslationOptionInline optionId={option.field_option_id} translations={option.translations} readOnly={readOnly} />
                      {!readOnly ? <button type="button" onClick={() => handleDeleteOption(option.field_option_id)}><Trash2 className="h-3.5 w-3.5 text-slate-400 hover:text-rose-600" /></button> : null}
                    </div>
                    {(field.field_type === "PICTURE_CHOICE" || field.field_type === "PEST" || field.field_type === "DISEASE") ? (
                      <div className="mt-2">
                        <SystemMediaField
                          targetType="FIELD_OPTION"
                          targetId={option.field_option_id}
                          assetRole="OPTION_IMAGE"
                          label="Farmer choice image"
                          accept="image/jpeg,image/png,image/webp"
                          readOnly={readOnly}
                          compact
                        />
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
              <div className="mt-2 flex gap-2">
                <Input
                  placeholder="OPTION_CODE"
                  value={newOptionCode}
                  onChange={(e) => setNewOptionCode(e.target.value)}
                  className="h-8 text-sm"
                />
                <Button size="sm" onClick={handleAddOption}>
                  Add option
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function TranslationOptionInline({ optionId, translations = [], readOnly }) {
  const [en, setEn] = useState(() => translations.find((item) => item.locale === "en-IN")?.label || "");
  const [or, setOr] = useState(() => translations.find((item) => item.locale === "or-IN")?.label || "");
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await Promise.all([
        upsertOptionTranslation(optionId, "en-IN", { label: en }),
        upsertOptionTranslation(optionId, "or-IN", { label: or }),
      ]);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex items-center gap-1">
      <Input placeholder="EN label" value={en} onChange={(e) => setEn(e.target.value)} className="h-7 w-24 text-xs" disabled={readOnly} />
      <Input placeholder="OR label" value={or} onChange={(e) => setOr(e.target.value)} className="h-7 w-24 text-xs" disabled={readOnly} />
      <Button size="sm" variant="outline" className="h-7 px-2 text-xs" onClick={save} disabled={saving || readOnly}>
        Save
      </Button>
    </div>
  );
}
