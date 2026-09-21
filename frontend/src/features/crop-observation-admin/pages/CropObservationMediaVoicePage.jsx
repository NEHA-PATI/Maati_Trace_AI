import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Music2, RefreshCw, Volume2 } from "lucide-react";

import {
  generateConfigurationAudio,
  generateStageInstructionAudio,
  getTtsStatus,
  listConfigurations,
  listStages,
  listCrops,
  listSystemMedia,
  listTtsProfiles,
  listTtsVoices,
  fetchTtsVoicePreview,
  resolveCropObservationServiceUrl,
  upsertTtsProfile,
  upsertStageTranslation,
} from "../api/cropObservationAdminApi";

export default function CropObservationMediaVoicePage() {
  const [status, setStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [profiles, setProfiles] = useState([]);
  const [voices, setVoices] = useState({ "or-IN": [], "en-IN": [] });
  const [voiceLoading, setVoiceLoading] = useState("");
  const [media, setMedia] = useState([]);
  const [crops, setCrops] = useState([]);
  const [cropCode, setCropCode] = useState("");
  const [configs, setConfigs] = useState([]);
  const [configId, setConfigId] = useState("");
  const [stages, setStages] = useState([]);
  const [stageLoading, setStageLoading] = useState(false);
  const [stageBusy, setStageBusy] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [previewUrls, setPreviewUrls] = useState({});

  async function reload() {
    setStatusLoading(true);
    const results = await Promise.allSettled([
      getTtsStatus(),
      listTtsProfiles(),
      listSystemMedia({ limit: 300 }),
      listCrops(),
    ]);
    const [statusResult, profilesResult, mediaResult, cropsResult] = results;
    if (statusResult.status === "fulfilled") setStatus(statusResult.value);
    if (profilesResult.status === "fulfilled") setProfiles(profilesResult.value);
    if (mediaResult.status === "fulfilled") setMedia(mediaResult.value);
    if (cropsResult.status === "fulfilled") {
      setCrops(cropsResult.value);
      if (!cropCode && cropsResult.value.length) setCropCode(cropsResult.value[0].crop_code);
    }
    setStatusLoading(false);
    const failure = results.find((result) => result.status === "rejected");
    if (failure) throw failure.reason;
  }

  useEffect(() => {
    reload().catch((err) => setMessage(err?.message || "Could not load media settings."));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!cropCode) return;
    listConfigurations(cropCode)
      .then((rows) => {
        setConfigs(rows);
        const preferred = rows.find((row) => row.status === "DRAFT");
        setConfigId(preferred?.config_version_id || "");
      })
      .catch(() => {
        setConfigs([]);
        setConfigId("");
      });
  }, [cropCode]);

  useEffect(() => {
    if (!configId) {
      setStages([]);
      return;
    }
    setStageLoading(true);
    listStages(configId)
      .then(setStages)
      .catch(() => setStages([]))
      .finally(() => setStageLoading(false));
  }, [configId]);

  useEffect(() => {
    let cancelled = false;
    async function loadPreviews() {
      const next = {};
      for (const locale of ["or-IN", "en-IN"]) {
        const profile = profiles.find((item) => item.locale === locale);
        const voice = voices[locale].find((item) => item.voice_id === profile?.voice_id);
        if (!voice?.voice_id || !voice.preview_url) continue;
        try {
          next[locale] = URL.createObjectURL(await fetchTtsVoicePreview(voice.voice_id));
        } catch { /* provider previews are optional */ }
      }
      if (!cancelled) setPreviewUrls(next);
      else Object.values(next).forEach((url) => URL.revokeObjectURL(url));
    }
    loadPreviews();
    return () => { cancelled = true; };
  }, [profiles, voices]);

  async function loadVoices(locale) {
    setVoiceLoading(locale);
    setMessage("");
    try {
      const list = await listTtsVoices(locale);
      setVoices((prev) => ({ ...prev, [locale]: list }));
    } catch (err) {
      setMessage(err?.message || "Could not load Cartesia voices.");
    } finally {
      setVoiceLoading("");
    }
  }

  async function saveVoice(locale, voiceId) {
    if (!voiceId) return;
    const selected = voices[locale].find((v) => v.voice_id === voiceId);
    setBusy(true);
    try {
      await upsertTtsProfile(locale, { voice_id: voiceId, voice_name: selected?.name || null });
      setProfiles(await listTtsProfiles());
      setMessage(`${locale === "or-IN" ? "Odia" : "English"} voice updated.`);
    } catch (err) {
      setMessage(err?.message || "Could not update voice.");
    } finally {
      setBusy(false);
    }
  }

  async function generateAll() {
    if (!configId) return;
    setBusy(true);
    setMessage("Generating missing/changed instruction audio…");
    try {
      const result = await generateConfigurationAudio(configId, { locales: ["en-IN", "or-IN"], force: false });
      setMessage(`${result.ready} instruction clips ready · ${result.failed} failed`);
      await reload();
    } catch (err) {
      setMessage(err?.message || "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveStageText(stage, locale, instructionText) {
    const translations = stage.translations || [];
    const current = translations.find((item) => item.locale === locale) || {};
    setStageBusy(`${stage.stage_id}:${locale}:save`);
    try {
      await upsertStageTranslation(stage.stage_id, locale, {
        display_name: current.display_name || stage.stage_code,
        instruction_text: instructionText.trim() || null,
      });
      setStages((previous) => previous.map((item) => item.stage_id !== stage.stage_id ? item : {
        ...item,
        translations: [
          ...(item.translations || []).filter((translation) => translation.locale !== locale),
          { ...current, locale, instruction_text: instructionText.trim() || null },
        ],
      }));
      setMessage(`${locale === "or-IN" ? "Odia" : "English"} text saved for ${stage.stage_code}.`);
    } catch (err) {
      setMessage(err?.message || "Could not save instruction text.");
    } finally {
      setStageBusy("");
    }
  }

  async function generateStage(stage, locale) {
    setStageBusy(`${stage.stage_id}:${locale}:generate`);
    setMessage("");
    try {
      await generateStageInstructionAudio(stage.stage_id, locale, { force: false });
      setMessage(`${locale === "or-IN" ? "Odia" : "English"} audio generated for ${stage.stage_code}.`);
      await reload();
    } catch (err) {
      setMessage(err?.message || "Could not generate instruction audio.");
    } finally {
      setStageBusy("");
    }
  }

  const audioRows = useMemo(() => media.filter((item) => item.asset_role === "INSTRUCTION_AUDIO"), [media]);
  const visualRows = useMemo(() => media.filter((item) => item.asset_role !== "INSTRUCTION_AUDIO"), [media]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-black text-slate-900">Instruction voice</h3>
            <p className="mt-1 max-w-2xl text-sm text-slate-500">Cartesia is used only while configuring content. Generated clips are stored once in LOCAL/S3 storage and are replayed by farmers without another TTS call.</p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-bold ${statusLoading ? "bg-slate-100 text-slate-600" : status?.api_key_configured ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
            {statusLoading ? "Checking Cartesia..." : status?.api_key_configured ? "Cartesia connected" : "Cartesia key missing"}
          </span>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-2">
          {["or-IN", "en-IN"].map((locale) => {
            const profile = profiles.find((p) => p.locale === locale);
            return (
              <div key={locale} className="rounded-xl border bg-slate-50 p-4">
                <div className="flex items-center gap-2"><Volume2 className="h-4 w-4 text-emerald-700" /><div className="font-bold text-slate-900">{locale === "or-IN" ? "Odia instruction voice" : "English instruction voice"}</div></div>
                <div className="mt-1 text-sm text-slate-500">Current: {profile?.voice_name || profile?.voice_id || "Not configured"}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button disabled={voiceLoading === locale} onClick={() => loadVoices(locale)} className="inline-flex items-center gap-1 rounded-lg border bg-white px-3 py-2 text-sm font-semibold disabled:opacity-50"><RefreshCw className="h-3.5 w-3.5" />{voiceLoading === locale ? "Loading…" : "Load voices"}</button>
                  {voices[locale].length ? (
                    <select className="h-10 min-w-[240px] flex-1 rounded-lg border bg-white px-2 text-sm" value={profile?.voice_id || ""} onChange={(e) => saveVoice(locale, e.target.value)} disabled={busy}>
                      <option value="">Choose voice…</option>
                      {voices[locale].map((v) => <option key={v.voice_id} value={v.voice_id}>{v.name}</option>)}
                    </select>
                  ) : null}
                </div>
                {previewUrls[locale] ? <audio controls preload="none" className="mt-3 h-9 w-full" src={previewUrls[locale]} /> : null}
              </div>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <h3 className="font-black text-slate-900">Generate crop instruction audio</h3>
        <p className="mt-1 text-sm text-slate-500">Write the instruction in English and Odia below, save it, then generate the audio. Farmers will hear the generated clip for their selected language.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-[240px_1fr_auto]">
          <select value={cropCode} onChange={(e) => setCropCode(e.target.value)} className="h-10 rounded-lg border bg-white px-3 text-sm font-semibold">
            {crops.map((crop) => <option key={crop.crop_code} value={crop.crop_code}>{crop.crop_code}</option>)}
          </select>
          <select value={configId} onChange={(e) => setConfigId(e.target.value)} className="h-10 rounded-lg border bg-white px-3 text-sm">
            {configs.map((config) => <option key={config.config_version_id} value={config.config_version_id}>v{config.version_number} · {config.status}</option>)}
          </select>
          <button disabled={!configId || configs.find((row) => row.config_version_id === configId)?.status !== "DRAFT" || busy} onClick={generateAll} className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">Generate missing / changed</button>
        </div>
        {!configId && configs.length ? <p className="mt-3 text-sm text-amber-700">Only draft configurations can generate audio. Clone the published configuration from the Configuration tab first.</p> : null}
        {message ? <p className="mt-3 text-sm font-medium text-slate-600">{message}</p> : null}
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="font-black text-slate-900">Instruction text</h3>
            <p className="mt-1 text-sm text-slate-500">Each stage has separate text for English and Odia. Audio can only be generated after text and a voice are configured.</p>
          </div>
          {stageLoading ? <span className="text-sm text-slate-500">Loading stages…</span> : null}
        </div>
        {!stageLoading && configId && !stages.length ? <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No stages exist in this draft configuration yet.</p> : null}
        <div className="mt-4 space-y-4">
          {stages.map((stage) => (
            <InstructionTextEditor
              key={stage.stage_id}
              stage={stage}
              busy={stageBusy}
              onSave={saveStageText}
              onGenerate={generateStage}
            />
          ))}
        </div>
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-2"><div><h3 className="font-black text-slate-900">Instruction audio assets</h3><p className="mt-1 text-sm text-slate-500">{audioRows.length} active bindings.</p></div><div className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700"><CheckCircle2 className="h-4 w-4" />stored media</div></div>
        <MediaTable rows={audioRows} />
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <h3 className="font-black text-slate-900">Configured visual media</h3>
        <p className="mt-1 text-sm text-slate-500">Crop, stage, practice and pest/disease option images are uploaded directly inside Configuration, next to the object they belong to.</p>
        <MediaTable rows={visualRows} />
      </section>
    </div>
  );
}

function InstructionTextEditor({ stage, busy, onSave, onGenerate }) {
  const english = stage.translations?.find((item) => item.locale === "en-IN")?.instruction_text || "";
  const odia = stage.translations?.find((item) => item.locale === "or-IN")?.instruction_text || "";
  const [values, setValues] = useState({ "en-IN": english, "or-IN": odia });

  useEffect(() => setValues({ "en-IN": english, "or-IN": odia }), [english, odia]);

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="font-bold text-slate-900">{stage.stage_code}</p>
        {stage.is_initial ? <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">initial</span> : null}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {[{ locale: "en-IN", label: "English" }, { locale: "or-IN", label: "ଓଡ଼ିଆ (Odia)" }].map(({ locale, label }) => {
          const saveKey = `${stage.stage_id}:${locale}:save`;
          const generateKey = `${stage.stage_id}:${locale}:generate`;
          return (
            <div key={locale} className="space-y-2">
              <label className="block text-xs font-bold text-slate-600">{label} speech text</label>
              <textarea
                value={values[locale]}
                onChange={(event) => setValues((previous) => ({ ...previous, [locale]: event.target.value }))}
                maxLength={1200}
                rows={4}
                placeholder={`Type the ${label} instruction that farmers should hear…`}
                className="w-full rounded-lg border bg-white px-3 py-2 text-sm outline-none ring-emerald-500 focus:ring-2"
              />
              <div className="flex flex-wrap items-center gap-2">
                <button type="button" disabled={!stage.config_version_id || busy === saveKey} onClick={() => onSave(stage, locale, values[locale])} className="rounded-lg border bg-white px-3 py-2 text-xs font-bold text-slate-700 disabled:opacity-50">
                  {busy === saveKey ? "Saving…" : "Save text"}
                </button>
                <button type="button" disabled={!values[locale].trim() || busy === generateKey} onClick={() => onGenerate(stage, locale)} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white disabled:opacity-50">
                  {busy === generateKey ? "Generating…" : "Generate audio"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MediaTable({ rows }) {
  if (!rows.length) return <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No active media yet.</p>;
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[850px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr>{["Role", "Target", "Locale", "Type", "Storage", "Preview"].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr></thead>
        <tbody className="divide-y">
          {rows.map((m) => {
            const url = resolveCropObservationServiceUrl(m.content_url);
            return <tr key={m.binding_id}><td className="px-3 py-2 font-semibold">{m.asset_role}</td><td className="px-3 py-2">{m.target_type} · {String(m.target_id).slice(0, 8)}</td><td className="px-3 py-2">{m.locale || "—"}</td><td className="px-3 py-2">{m.mime_type}</td><td className="px-3 py-2">{m.storage_backend}</td><td className="px-3 py-2">{m.mime_type?.startsWith("audio/") ? <audio controls preload="none" src={url} className="h-8 w-52" /> : <img src={url} alt="" className="h-10 w-16 rounded object-cover" />}</td></tr>;
          })}
        </tbody>
      </table>
    </div>
  );
}
