import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { generateStageInstructionAudio, upsertStageTranslation } from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import SystemMediaField from "./SystemMediaField";

/**
 * One block per stage: speech text (EN + Odia) and its audio clips.
 * Typing text and pressing "Save text" invalidates the derived clip in the
 * backend — the stale chip below tells the admin to regenerate.
 */
export default function InstructionAudio({ stage, workflow }) {
  const initialEn = stage.translations?.find((t) => t.locale === "en-IN") || {};
  const initialOr = stage.translations?.find((t) => t.locale === "or-IN") || {};
  const [text, setText] = useState({
    "en-IN": initialEn.instruction_text || "",
    "or-IN": initialOr.instruction_text || "",
  });
  const [busy, setBusy] = useState("");
  const [status, setStatus] = useState("");
  const [savedText, setSavedText] = useState({
    "en-IN": initialEn.instruction_text || "",
    "or-IN": initialOr.instruction_text || "",
  });
  const [mediaTick, setMediaTick] = useState(0);

  useEffect(() => {
    setText({ "en-IN": initialEn.instruction_text || "", "or-IN": initialOr.instruction_text || "" });
    setSavedText({ "en-IN": initialEn.instruction_text || "", "or-IN": initialOr.instruction_text || "" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage.stage_id]);

  function isStale(locale) {
    // Backend drops the clip binding when text changes after generation.
    // If the admin edited text here but hasn't regenerated, flag it.
    return (savedText[locale] || "") !== (text[locale] || "") && (text[locale] || "").trim() !== "";
  }

  async function saveText(locale) {
    setBusy(`${locale}:save`);
    setStatus("");
    try {
      const translations = locale === "en-IN" ? initialEn : initialOr;
      await upsertStageTranslation(stage.stage_id, locale, {
        display_name: translations.display_name || stage.stage_code,
        short_description: translations.short_description || null,
        instruction_text: text[locale].trim() || null,
      });
      setSavedText((prev) => ({ ...prev, [locale]: text[locale] }));
      setStatus(`Saved ${locale === "or-IN" ? "Odia" : "English"} text`);
      await workflow?.changed();
    } catch (error) {
      setStatus(error?.message || "Could not save text.");
    } finally {
      setBusy("");
    }
  }

  async function generate(locale) {
    setBusy(`${locale}:gen`);
    setStatus("");
    try {
      await workflow?.ensureEditable();
      await generateStageInstructionAudio(stage.stage_id, locale, { force: false });
      setStatus(`Generated ${locale === "or-IN" ? "Odia" : "English"} audio`);
      setMediaTick((t) => t + 1);
      await workflow?.changed();
    } catch (error) {
      setStatus(error?.message || "Could not generate audio.");
    } finally {
      setBusy("");
    }
  }

  const locales = [
    { locale: "en-IN", label: "English" },
    { locale: "or-IN", label: "ଓଡ଼ିଆ (Odia)" },
  ];

  return (
    <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-3">
      <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">Instruction audio</p>
      <p className="mt-1 text-xs text-slate-500">Type what farmers should hear, then generate it — or upload your own recording.</p>

      <div className="mt-3 space-y-3">
        {locales.map(({ locale, label }) => (
          <div key={locale} className="rounded-lg border border-emerald-100 bg-white p-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className="text-xs font-bold text-slate-600">{label}</label>
              {isStale(locale) ? (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700">text changed — save & regenerate</span>
              ) : null}
            </div>
            <textarea
              value={text[locale]}
              onChange={(e) => setText((prev) => ({ ...prev, [locale]: e.target.value }))}
              maxLength={1200}
              rows={2}
              placeholder={`Type the ${label} instruction…`}
              className="mt-1 w-full rounded-md border px-2 py-1.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_auto] sm:items-center">
              <SystemMediaField
                key={`${locale}-${mediaTick}`}
                targetType="STAGE"
                targetId={stage.stage_id}
                assetRole="INSTRUCTION_AUDIO"
                locale={locale}
                label={`${label} clip`}
                accept="audio/mpeg,audio/wav,audio/ogg,audio/mp4"
                compact
              />
              <div className="flex gap-1.5">
                <Button size="sm" variant="outline" disabled={busy === `${locale}:save`} onClick={() => saveText(locale)}>
                  {busy === `${locale}:save` ? "Saving…" : "Save text"}
                </Button>
                <Button size="sm" disabled={busy === `${locale}:gen` || !(text[locale] || "").trim()} onClick={() => generate(locale)}>
                  {busy === `${locale}:gen` ? "Generating…" : "Generate"}
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {status ? <p className="mt-2 text-xs font-medium text-slate-600">{status}</p> : null}
    </div>
  );
}
