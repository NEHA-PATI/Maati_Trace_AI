import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, Smartphone, Monitor, Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import LoadingState from "@/components/ui/LoadingState";
import { Input } from "@/components/ui/input";
import {
  createStage,
  getCrop,
  listPracticeTemplates,
  getTtsStatus,
  listTtsProfiles,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import useConfigWorkflow from "@/features/crop-observation-admin/hooks/useConfigWorkflow";
import StageEditor from "@/features/crop-observation-admin/components/StageEditor";
import VoicePicker from "@/features/crop-observation-admin/components/VoicePicker";

export default function CropConfigurationEditorPage() {
  const { cropCode } = useParams();
  const navigate = useNavigate();

  const [crop, setCrop] = useState(null);
  const [practiceTemplates, setPracticeTemplates] = useState([]);
  const [ttsStatus, setTtsStatus] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [staticError, setStaticError] = useState("");
  const [previewMobile, setPreviewMobile] = useState(true);
  const [newStageCode, setNewStageCode] = useState("");
  const [addingStage, setAddingStage] = useState(false);

  const workflow = useConfigWorkflow(cropCode);
  const { stages, validation, isEditing, readOnly, canPublish, publishing, justPublished, loading } = workflow;

  useEffect(() => {
    let cancelled = false;
    Promise.all([getCrop(cropCode), listPracticeTemplates(), getTtsStatus(), listTtsProfiles()])
      .then(([cropData, templates, tts, ttsProfiles]) => {
        if (cancelled) return;
        setCrop(cropData);
        setPracticeTemplates(templates);
        setTtsStatus(tts);
        setProfiles(ttsProfiles);
      })
      .catch((err) => {
        if (!cancelled) setStaticError(err?.message || "Could not load crop.");
      });
    return () => {
      cancelled = true;
    };
  }, [cropCode]);

  async function handleAddStage() {
    const code = newStageCode.trim().toLowerCase().replace(/\s+/g, "_");
    if (!code) return;
    setAddingStage(true);
    workflow.setError("");
    try {
      const configId = await workflow.ensureEditable();
      if (!configId) return;
      await createStage(configId, {
        stage_code: code,
        display_order: stages.length,
        is_initial: stages.length === 0,
      });
      setNewStageCode("");
      await workflow.changed();
    } catch (err) {
      workflow.setError(err?.message || "Could not add stage.");
    } finally {
      setAddingStage(false);
    }
  }

  async function handlePublish() {
    await workflow.publish();
  }

  const publishBlockedReason = !isEditing
    ? null
    : !validation
      ? "Checking…"
      : !validation.valid
        ? validation.errors?.[0]
          ? `Fix: ${validation.errors[0].code}${validation.errors[0].stage_code ? ` (${validation.errors[0].stage_code})` : ""}`
          : "Fix validation errors first"
        : null;

  if (loading) {
    return <LoadingState label="Loading configuration…" className="px-4 py-8 text-sm text-slate-400" />;
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <button
        type="button"
        onClick={() => navigate("/admin/crop-observation?tab=configuration")}
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800"
      >
        <ChevronLeft className="h-4 w-4" /> Back to crops
      </button>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-black text-slate-950">{cropCode}</h1>
          {publishedLabel(workflow)}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPreviewMobile((v) => !v)}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600"
          >
            {previewMobile ? <Smartphone className="h-3.5 w-3.5" /> : <Monitor className="h-3.5 w-3.5" />}
            {previewMobile ? "Mobile" : "Desktop"}
          </button>
        </div>
      </div>

      {staticError ? <p className="mt-2 text-sm text-rose-600">{staticError}</p> : null}
      {workflow.error ? <p className="mt-2 text-sm text-rose-600">{workflow.error}</p> : null}
      {crop && crop.is_active === false ? (
        <p className="mt-2 text-sm text-amber-600">This crop is inactive — farmers won't see it in the catalogue.</p>
      ) : null}
      {justPublished ? (
        <p className="mt-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
          ✓ Changes published — new crop cycles use the updated flow.
        </p>
      ) : null}

      {/* Keep the editing flow focused on the crop lifecycle, not version bookkeeping. */}
      <div className="sticky top-2 z-10 mt-4 rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-sm backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm">
            {isEditing ? (
              validation?.valid ? (
                <span className="font-semibold text-emerald-700">✓ Ready to publish</span>
              ) : (
                <span className="font-medium text-slate-600">{publishBlockedReason || "Editing — changes go live when you publish."}</span>
              )
            ) : (
              <span className="inline-flex items-center gap-1.5 text-slate-500">
                <Pencil className="h-3.5 w-3.5" /> Viewing the live configuration
              </span>
            )}
          </div>
          {isEditing ? (
            <Button onClick={handlePublish} disabled={!canPublish}>
              {publishing ? "Publishing…" : "Publish changes"}
            </Button>
          ) : (
            <Button variant="outline" onClick={() => workflow.startEditing()}>Edit configuration</Button>
          )}
        </div>
        {validation && !validation.valid && isEditing ? (
          <div className="mt-2 space-y-0.5 text-xs">
            {validation.errors.map((issue, i) => (
              <p key={i} className="text-rose-600">
                ✕ {issue.code}{issue.stage_code ? ` (${issue.stage_code})` : ""}{issue.field_code ? ` — ${issue.field_code}` : ""}
              </p>
            ))}
            {validation.warnings.map((issue, i) => (
              <p key={i} className="text-amber-600">⚠ {issue.code}{issue.stage_code ? ` (${issue.stage_code})` : ""}</p>
            ))}
          </div>
        ) : null}
      </div>

      {/* Voice setup — pick by listening, no provider IDs. Applies at generation time. */}
      <div className="mt-6 rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">Instruction voices</p>
            <p className="text-xs text-slate-500">
              Pick the voice farmers hear. {ttsStatus?.api_key_configured ? "Cartesia connected." : "Cartesia API key missing — generation disabled."}
            </p>
          </div>
          <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
            {ttsStatus?.model_id || "No model"}
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {["en-IN", "or-IN"].map((locale) => (
            <VoicePicker
              key={locale}
              locale={locale}
              profile={profiles.find((p) => p.locale === locale)}
              onSaved={async () => setProfiles(await listTtsProfiles())}
            />
          ))}
        </div>
      </div>

      <div className={`mx-auto mt-6 ${previewMobile ? "max-w-[390px] rounded-3xl border-4 border-slate-800 p-2" : ""}`}>
        <div className="space-y-3">
          {stages.length === 0 ? (
            <p className="text-sm text-slate-400">
              {readOnly ? "No stages in the live configuration — edit to add some." : "No stages yet — add the first one below."}
            </p>
          ) : null}
          {stages.map((stage) => (
            <StageEditor
              key={stage.stage_id}
              stage={stage}
              practiceTemplates={practiceTemplates}
              workflow={workflow}
            />
          ))}

          {!readOnly ? (
            <div className="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 p-3">
              <Input
                placeholder="New stage name (e.g. flowering)"
                value={newStageCode}
                onChange={(e) => setNewStageCode(e.target.value)}
                className="h-8 text-sm"
                onKeyDown={(e) => { if (e.key === "Enter") handleAddStage(); }}
              />
              <Button size="sm" onClick={handleAddStage} disabled={addingStage}>
                {addingStage ? "Adding…" : "Add stage"}
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function publishedLabel(workflow) {
  if (workflow.isEditing) {
    return <p className="text-sm text-amber-700">Draft in progress — your updates are saved here and published when ready.</p>;
  }
  if (workflow.published) {
    return <p className="text-sm text-slate-500">Published and available to farmers.</p>;
  }
  return <p className="text-sm text-slate-500">Not published yet.</p>;
}
