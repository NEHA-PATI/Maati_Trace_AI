import { useEffect, useState } from "react";
import { getCropObservationSystemStatus } from "../api/cropObservationAdminApi";

export default function CropObservationSystemPage() {
  const [data, setData] = useState(null);
  useEffect(() => { getCropObservationSystemStatus().then(setData); }, []);
  if (!data) return <div className="h-64 animate-pulse rounded-2xl bg-slate-100" />;
  const rows = [
    ['Service', data.service], ['Environment', data.environment], ['Storage backend', data.storage_backend], ['S3 bucket', data.s3_bucket || 'Not configured'], ['Cartesia key', data.cartesia_key_configured ? 'Configured' : 'Missing'], ['TTS model', data.tts_model], ['System assets ready', data.system_assets_ready], ['TTS ready', data.tts_ready], ['TTS failed', data.tts_failed], ['Outbox pending', data.outbox_pending], ['Open flags', data.open_flags],
  ];
  return <div className="rounded-2xl border bg-white p-5 shadow-sm"><h3 className="font-black text-slate-900">Crop Observation system</h3><div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{rows.map(([k,v])=><div key={k} className="rounded-xl border bg-slate-50 p-3"><div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{k}</div><div className="mt-1 break-all text-sm font-bold text-slate-900">{String(v)}</div></div>)}</div></div>;
}
