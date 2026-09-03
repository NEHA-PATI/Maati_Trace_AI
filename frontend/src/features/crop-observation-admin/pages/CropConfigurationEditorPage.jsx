import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, Smartphone, Monitor } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  cloneConfiguration,
  createDraftConfiguration,
  createStage,
  getTtsStatus,
  listTtsProfiles,
  getCrop,
  listConfigurations,
  listPracticeTemplates,
  listStages,
  publishConfiguration,
  upsertTtsProfile,
  validateConfiguration,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import StageEditor from "@/features/crop-observation-admin/components/StageEditor";

export default function CropConfigurationEditorPage() {
  const { cropCode } = useParams();
  const navigate = useNavigate();

  const [crop, setCrop] = useState(null);
  const [configs, setConfigs] = useState([]);
  const [selectedConfigId, setSelectedConfigId] = useState("");
  const [stages, setStages] = useState([]);
  const [practiceTemplates, setPracticeTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [validation, setValidation] = useState(null);
  const [previewMobile, setPreviewMobile] = useState(true);
  const [newStageCode, setNewStageCode] = useState("");
  const [ttsStatus, setTtsStatus] = useState(null);
  const [ttsProfiles, setTtsProfiles] = useState([]);
  const [voiceDrafts, setVoiceDrafts] = useState({
    "en-IN": { voice_id: "", voice_name: "" },
    "or-IN": { voice_id: "", voice_name: "" },
  });

  const selectedConfig = configs.find((c) => c.config_version_id === selectedConfigId);
  const isDraft = selectedConfig?.status === "DRAFT";

  const loadStages = useCallback(async (configId) => {
    if (!configId) {
      setStages([]);
      return;
    }
    setStages(await listStages(configId));
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [cropData, configList, templates] = await Promise.all([
        getCrop(cropCode),
        listConfigurations(cropCode),
        listPracticeTemplates(),
      ]);
      const [ttsStatusData, ttsProfileData] = await Promise.all([getTtsStatus(), listTtsProfiles()]);
      setCrop(cropData);
      setConfigs(configList);
      setPracticeTemplates(templates);
      setTtsStatus(ttsStatusData);
      setTtsProfiles(ttsProfileData);
      setVoiceDrafts({
        "en-IN": {
          voice_id: ttsProfileData.find((item) => item.locale === "en-IN")?.voice_id || "",
          voice_name: ttsProfileData.find((item) => item.locale === "en-IN")?.voice_name || "",
        },
        "or-IN": {
          voice_id: ttsProfileData.find((item) => item.locale === "or-IN")?.voice_id || "",
          voice_name: ttsProfileData.find((item) => item.locale === "or-IN")?.voice_name || "",
        },
      });
      const preferred = configList.find((c) => c.status === "DRAFT") || configList[0];
      if (preferred) {
        setSelectedConfigId(preferred.config_version_id);
        await loadStages(preferred.config_version_id);
      }
    } catch (err) {
      setError(err?.message || "Could not load configuration.");
    } finally {
      setLoading(false);
    }
  }, [cropCode, loadStages]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  async function handleSelectConfig(id) {
    setSelectedConfigId(id);
    setValidation(null);
    await loadStages(id);
  }

  async function handleCreateDraft() {
    setBusy(true);
    setError("");
    try {
      const draft = await createDraftConfiguration(cropCode);
      await loadAll();
      setSelectedConfigId(draft.config_version_id);
      await loadStages(draft.config_version_id);
    } catch (err) {
      setError(err?.message || "Could not create draft.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCloneAsDraft() {
    if (!selectedConfigId) return;
    setBusy(true);
    setError("");
    try {
      const draft = await cloneConfiguration(selectedConfigId);
      await loadAll();
      setSelectedConfigId(draft.config_version_id);
      await loadStages(draft.config_version_id);
    } catch (err) {
      setError(err?.message || "Could not clone configuration.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddStage() {
    if (!newStageCode.trim()) return;
    const created = await createStage(selectedConfigId, {
      stage_code: newStageCode.trim(),
      display_order: stages.length,
      is_initial: stages.length === 0,
    });
    setStages((prev) => [...prev, created]);
    setNewStageCode("");
  }

  function handleStageDeleted(stageId) {
    setStages((prev) => prev.filter((s) => s.stage_id !== stageId));
  }

  async function handleValidate() {
    setBusy(true);
    try {
      setValidation(await validateConfiguration(selectedConfigId));
    } catch (err) {
      setError(err?.message || "Could not validate.");
    } finally {
      setBusy(false);
    }
  }

  async function handlePublish() {
    setBusy(true);
    setError("");
    try {
      await publishConfiguration(selectedConfigId);
      await loadAll();
    } catch (err) {
      if (Array.isArray(err?.fields) && err.fields.length) {
        setValidation({ valid: false, errors: err.fields, warnings: [] });
      }
      setError(err?.message || "Could not publish.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveVoice(locale) {
    setBusy(true);
    setError("");
    try {
      await upsertTtsProfile(locale, voiceDrafts[locale]);
      setTtsProfiles(await listTtsProfiles());
    } catch (err) {
      setError(err?.message || "Could not save TTS profile.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="px-4 py-8 text-sm text-slate-400">Loading…</div>;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <button
        type="button"
        onClick={() => navigate("/admin/crop-observations/config")}
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800"
      >
        <ChevronLeft className="h-4 w-4" /> Back to crops
      </button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-slate-950">{cropCode}</h1>
        <button
          type="button"
          onClick={() => setPreviewMobile((v) => !v)}
          className="flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600"
        >
          {previewMobile ? <Smartphone className="h-3.5 w-3.5" /> : <Monitor className="h-3.5 w-3.5" />}
          {previewMobile ? "Mobile" : "Desktop"}
        </button>
      </div>

      {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
      {!crop?.is_active ? (
        <p className="mt-2 text-sm text-amber-600">This crop is inactive — farmers won't see it in the catalogue.</p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <select
          value={selectedConfigId}
          onChange={(e) => handleSelectConfig(e.target.value)}
          className="h-9 rounded-md border border-slate-200 px-2 text-sm"
        >
          {configs.map((c) => (
            <option key={c.config_version_id} value={c.config_version_id}>
              v{c.version_number} — {c.status}
            </option>
          ))}
        </select>
        <Button size="sm" variant="outline" onClick={handleCreateDraft} disabled={busy}>
          New blank draft
        </Button>
        {selectedConfigId ? (
          <Button size="sm" variant="outline" onClick={handleCloneAsDraft} disabled={busy}>
            Clone as draft
          </Button>
        ) : null}
      </div>

      <div className="mt-6 rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">Cartesia instruction audio</p>
            <p className="text-xs text-slate-500">
              Status: {ttsStatus?.enabled ? "enabled" : "disabled"} · API key {ttsStatus?.api_key_configured ? "configured" : "missing"}
            </p>
          </div>
          <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
            {ttsStatus?.model_id || "No model"}
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {["en-IN", "or-IN"].map((locale) => (
            <div key={locale} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{locale}</p>
              <Input
                className="mt-2"
                placeholder="Voice ID"
                value={voiceDrafts[locale]?.voice_id || ""}
                onChange={(event) =>
                  setVoiceDrafts((prev) => ({
                    ...prev,
                    [locale]: { ...(prev[locale] || {}), voice_id: event.target.value },
                  }))
                }
              />
              <Input
                className="mt-2"
                placeholder="Voice name"
                value={voiceDrafts[locale]?.voice_name || ""}
                onChange={(event) =>
                  setVoiceDrafts((prev) => ({
                    ...prev,
                    [locale]: { ...(prev[locale] || {}), voice_name: event.target.value },
                  }))
                }
              />
              <Button size="sm" variant="outline" className="mt-2" onClick={() => handleSaveVoice(locale)} disabled={busy}>
                Save voice
              </Button>
            </div>
          ))}
        </div>
      </div>

      <div
        className={`mx-auto mt-6 ${previewMobile ? "max-w-[390px] rounded-3xl border-4 border-slate-800 p-2" : ""}`}
      >
        <div className="space-y-3">
          {stages.length === 0 ? (
            <p className="text-sm text-slate-400">
              {selectedConfigId ? "No stages yet." : "No configuration selected — create a draft to begin."}
            </p>
          ) : null}
          {stages.map((stage) => (
            <StageEditor
              key={stage.stage_id}
              stage={stage}
              practiceTemplates={practiceTemplates}
              onDeleted={handleStageDeleted}
              readOnly={!isDraft}
            />
          ))}

          {isDraft ? (
            <div className="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 p-3">
              <Input
                placeholder="stage_code"
                value={newStageCode}
                onChange={(e) => setNewStageCode(e.target.value)}
                className="h-8 text-sm"
              />
              <Button size="sm" onClick={handleAddStage}>
                Add stage
              </Button>
            </div>
          ) : null}
        </div>
      </div>

      {isDraft ? (
        <div className="mt-8 space-y-3 border-t border-slate-100 pt-6">
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleValidate} disabled={busy}>
              Validate
            </Button>
            <Button onClick={handlePublish} disabled={busy}>
              Publish
            </Button>
          </div>

          {validation ? (
            <div className="space-y-1 text-sm">
              <p className={validation.valid ? "text-emerald-600" : "text-rose-600"}>
                {validation.valid ? "✓ Valid — ready to publish." : "✕ Not ready to publish."}
              </p>
              {validation.errors.map((issue, i) => (
                <p key={i} className="text-rose-600">
                  ✕ {issue.code} {issue.stage_code ? `(${issue.stage_code})` : ""}{" "}
                  {issue.field_code ? `— ${issue.field_code}` : ""}
                </p>
              ))}
              {validation.warnings.map((issue, i) => (
                <p key={i} className="text-amber-600">
                  ⚠ {issue.code} {issue.stage_code ? `(${issue.stage_code})` : ""}
                </p>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
