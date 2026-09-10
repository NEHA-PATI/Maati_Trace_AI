import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** A small en-IN / or-IN label editor used everywhere in the config
 * editor. `fields` describes the extra text inputs beyond the required
 * label/display_name (e.g. help_text, short_description). */
export default function TranslationFields({ initialEn, initialOr, onSave, labelKey = "label", extraFields = [] }) {
  const [en, setEn] = useState(initialEn || {});
  const [or, setOr] = useState(initialOr || {});
  const [saving, setSaving] = useState(false);

  useEffect(() => setEn(initialEn || {}), [initialEn]);
  useEffect(() => setOr(initialOr || {}), [initialOr]);

  async function handleSave() {
    setSaving(true);
    try {
      await Promise.all([onSave("en-IN", en), onSave("or-IN", or)]);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="space-y-2">
        <p className="text-xs font-semibold text-slate-500">English</p>
        <Input
          placeholder="Label"
          value={en[labelKey] || ""}
          onChange={(e) => setEn((prev) => ({ ...prev, [labelKey]: e.target.value }))}
        />
        {extraFields.map((field) => (
          <Input
            key={field}
            placeholder={field}
            value={en[field] || ""}
            onChange={(e) => setEn((prev) => ({ ...prev, [field]: e.target.value }))}
          />
        ))}
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold text-slate-500">ଓଡ଼ିଆ (Odia)</p>
        <Input
          placeholder="Label"
          value={or[labelKey] || ""}
          onChange={(e) => setOr((prev) => ({ ...prev, [labelKey]: e.target.value }))}
        />
        {extraFields.map((field) => (
          <Input
            key={field}
            placeholder={field}
            value={or[field] || ""}
            onChange={(e) => setOr((prev) => ({ ...prev, [field]: e.target.value }))}
          />
        ))}
      </div>
      <div className="col-span-2">
        <Button size="sm" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save translations"}
        </Button>
      </div>
    </div>
  );
}
