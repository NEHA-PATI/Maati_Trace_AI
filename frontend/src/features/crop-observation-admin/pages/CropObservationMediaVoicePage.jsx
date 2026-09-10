import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Music2, RefreshCw, Volume2 } from "lucide-react";

import {
  generateConfigurationAudio,
  getTtsStatus,
  listConfigurations,
  listCrops,
  listSystemMedia,
  listTtsProfiles,
  listTtsVoices,
  resolveCropObservationServiceUrl,
  upsertTtsProfile,
} from "../api/cropObservationAdminApi";

export default function CropObservationMediaVoicePage() {
  const [status, setStatus] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [voices, setVoices] = useState({ "or-IN": [], "en-IN": [] });
  const [voiceLoading, setVoiceLoading] = useState("");
  const [media, setMedia] = useState([]);
  const [crops, setCrops] = useState([]);
  const [cropCode, setCropCode] = useState("");
  const [configs, setConfigs] = useState([]);
  const [configId, setConfigId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    const [s, p, m, cropRows] = await Promise.all([
      getTtsStatus(),
      listTtsProfiles(),
      listSystemMedia({ limit: 300 }),
      listCrops(),
    ]);
    setStatus(s);
    setProfiles(p);
    setMedia(m);
    setCrops(cropRows);
    if (!cropCode && cropRows.length) setCropCode(cropRows[0].crop_code);
  }

  useEffect(() => {
    reload().catch((err) => setMessage(err?.message || "Could not load media settings."));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!cropCode) return;
    listConfigurations(cropCode)
      .then((rows) => {
        setConfigs(rows);
        const preferred = rows.find((row) => row.status === "DRAFT") || rows.find((row) => row.status === "PUBLISHED") || rows[0];
        setConfigId(preferred?.config_version_id || "");
      })
      .catch(() => {
        setConfigs([]);
        setConfigId("");
      });
  }, [cropCode]);

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
          <span className={`rounded-full px-3 py-1 text-xs font-bold ${status?.api_key_configured ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
            {status?.api_key_configured ? "Cartesia connected" : "Cartesia key missing"}
          </span>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-2">
          {["or-IN", "en-IN"].map((locale) => {
            const profile = profiles.find((p) => p.locale === locale);
            const selected = voices[locale].find((voice) => voice.voice_id === profile?.voice_id);
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
                {selected?.preview_url ? <audio controls preload="none" className="mt-3 h-9 w-full" src={selected.preview_url} /> : null}
              </div>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <h3 className="font-black text-slate-900">Generate crop instruction audio</h3>
        <p className="mt-1 text-sm text-slate-500">Select a crop/configuration. Only missing or changed text/voice combinations call Cartesia; unchanged content reuses the TTS cache.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-[240px_1fr_auto]">
          <select value={cropCode} onChange={(e) => setCropCode(e.target.value)} className="h-10 rounded-lg border bg-white px-3 text-sm font-semibold">
            {crops.map((crop) => <option key={crop.crop_code} value={crop.crop_code}>{crop.crop_code}</option>)}
          </select>
          <select value={configId} onChange={(e) => setConfigId(e.target.value)} className="h-10 rounded-lg border bg-white px-3 text-sm">
            {configs.map((config) => <option key={config.config_version_id} value={config.config_version_id}>v{config.version_number} · {config.status}</option>)}
          </select>
          <button disabled={!configId || busy} onClick={generateAll} className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">Generate missing / changed</button>
        </div>
        {message ? <p className="mt-3 text-sm font-medium text-slate-600">{message}</p> : null}
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
