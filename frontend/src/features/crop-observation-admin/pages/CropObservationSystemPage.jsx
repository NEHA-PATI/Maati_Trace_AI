import { useEffect, useState } from "react";
import { getCropObservationSystemDiagnostics, getCropObservationSystemStatus } from "../api/cropObservationAdminApi";

export default function CropObservationSystemPage() {
  const [data, setData] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);
  const [checking, setChecking] = useState(false);
  useEffect(() => { getCropObservationSystemStatus().then(setData); }, []);
  if (!data) return <div className="h-64 animate-pulse rounded-2xl bg-slate-100" />;
  async function runDiagnostics() {
    setChecking(true);
    try { setDiagnostics(await getCropObservationSystemDiagnostics()); } finally { setChecking(false); }
  }
  const rows = [
    ['Service', data.service], ['Environment', data.environment], ['Storage backend', data.storage_backend], ['S3 bucket', data.s3_bucket || 'Not configured'], ['Cartesia key', data.cartesia_key_configured ? 'Configured' : 'Missing'], ['TTS model', data.tts_model], ['System assets ready', data.system_assets_ready], ['TTS ready', data.tts_ready], ['TTS failed', data.tts_failed], ['Outbox pending', data.outbox_pending], ['Open flags', data.open_flags],
  ];
  return <div className="space-y-4"><div className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-center justify-between gap-3"><h3 className="font-black text-slate-900">Crop Observation system</h3><button type="button" onClick={runDiagnostics} disabled={checking} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white disabled:opacity-50">{checking ? "Checking…" : "Run diagnostics"}</button></div><div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{rows.map(([k,v])=><div key={k} className="rounded-xl border bg-slate-50 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{k}</div><div className="mt-1 break-all text-sm font-bold text-slate-900">{String(v)}</div></div>)}</div></div>{diagnostics ? <div className="rounded-2xl border bg-white p-5 shadow-sm"><h3 className="font-black text-slate-900">Live checks</h3><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{Object.entries(diagnostics).map(([key, check]) => <div key={key} className="rounded-xl border bg-slate-50 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{key.replaceAll("_", " ")}</div><div className={`mt-1 text-sm font-bold ${check.status === "PASS" ? "text-emerald-700" : check.status === "SKIPPED" ? "text-amber-700" : "text-rose-700"}`}>{check.status}</div><p className="mt-1 text-xs text-slate-500">{check.message}</p></div>)}</div></div> : null}</div>;
}
