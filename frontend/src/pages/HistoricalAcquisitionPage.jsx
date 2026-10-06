import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Database, RefreshCw, Satellite, Play, Ban, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  cancelAcquisitionJob, getAcquisitionJob, getAcquisitionJobs, getAcquisitionShards,
  getAcquisitionSources, previewAcquisition, retryAcquisitionJob, submitAcquisition,
} from "@/lib/api/mlAcquisition";

const INITIAL = {
  area_id: "district-odisha-block-01", boundary_version: "boundary-sha256-v1",
  bbox: "83.8,21.3,83.9,21.4", start: "2020-01-01", end: "2020-01-31",
  sources: ["sentinel_2_l2a", "landsat_c2_l2", "gpm_imerg_final"],
  mode: "retrospective", stage: "catalog_only", storage_uri: "file:///absolute/path/to/lakehouse",
};

function toPayload(form) {
  return { ...form, bbox: form.bbox.split(",").map(Number) };
}

export default function HistoricalAcquisitionPage() {
  const [sources, setSources] = useState([]); const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState(null); const [shards, setShards] = useState([]);
  const [form, setForm] = useState(INITIAL); const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const load = async () => { try { setError(""); setJobs((await getAcquisitionJobs()).jobs || []); } catch (e) { setError(e.message); } };
  useEffect(() => { getAcquisitionSources().then((data) => setSources(data.sources || [])).catch((e) => setError(e.message)); load(); }, []);
  const run = async (action) => { try { setBusy(true); setError(""); const data = action === "preview" ? await previewAcquisition(toPayload(form)) : await submitAcquisition(toPayload(form)); if (action === "preview") setPreview(data); else { setPreview(null); await load(); } } catch (e) { setError(e.message); } finally { setBusy(false); } };
  const inspect = async (job) => { try { setSelected(await getAcquisitionJob(job.job_id)); setShards((await getAcquisitionShards(job.job_id)).shards || []); } catch (e) { setError(e.message); } };
  const manage = async (action) => { if (!selected) return; try { setBusy(true); if (action === "retry") await retryAcquisitionJob(selected.job_id); else await cancelAcquisitionJob(selected.job_id); await load(); setSelected(null); } catch (e) { setError(e.message); } finally { setBusy(false); } };
  const selectedSet = useMemo(() => new Set(form.sources), [form.sources]);
  return <div className="mx-auto max-w-[1500px] space-y-5 p-4 md:p-6">
    <div className="flex flex-wrap items-end justify-between gap-3"><div><Link to="/admin" className="text-xs font-bold text-emerald-700"><ArrowLeft className="mr-1 inline h-3 w-3" />Admin</Link><h1 className="mt-2 text-3xl font-black text-slate-950">Data Acquisition</h1><p className="mt-1 text-sm text-slate-500">Phase 1 historical source planning, archiving and recovery.</p></div><Button variant="outline" onClick={load}><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button></div>
    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center gap-2"><Satellite className="h-5 w-5 text-emerald-600" /><h2 className="font-black">New campaign</h2></div>
        <div className="grid gap-3 md:grid-cols-2">{[["area_id","Area ID"],["boundary_version","Boundary version"],["bbox","Bounding box (west,south,east,north)"],["storage_uri","Storage URI"],["start","Start date"],["end","End date"]].map(([key,label]) => <label key={key} className="space-y-1 text-xs font-bold text-slate-600">{label}<input type={key === "start" || key === "end" ? "date" : "text"} value={form[key]} onChange={(e) => update(key,e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-800" /></label>)}</div>
        <div className="mt-4 grid gap-3 md:grid-cols-2"><label className="space-y-1 text-xs font-bold text-slate-600">Stage<select value={form.stage} onChange={(e)=>update("stage",e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal"><option value="catalog_only">Catalog only</option><option value="archive">Archive science assets</option></select></label><label className="space-y-1 text-xs font-bold text-slate-600">Mode<select value={form.mode} onChange={(e)=>update("mode",e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal"><option value="retrospective">Retrospective</option><option value="as_issued">As issued (requires source evidence)</option></select></label></div>
        <fieldset className="mt-4"><legend className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">Source contracts ({form.sources.length})</legend><div className="grid gap-2 sm:grid-cols-2">{sources.map((source)=><label key={source.key} className="flex items-start gap-2 rounded-lg border border-slate-100 p-2 text-xs"><input type="checkbox" checked={selectedSet.has(source.key)} onChange={(e)=>update("sources",e.target.checked?[...form.sources,source.key]:form.sources.filter((v)=>v!==source.key))}/><span><b>{source.key}</b><br/><span className="text-slate-400">{source.adapter}{source.requires_manifest?" · manifest required":""}</span></span></label>)}</div></fieldset>
        <div className="mt-5 flex flex-wrap gap-2"><Button variant="outline" disabled={busy} onClick={()=>run("preview")}><Database className="mr-2 h-4 w-4"/>Preview batches</Button><Button disabled={busy} onClick={()=>run("submit")}><Play className="mr-2 h-4 w-4"/>Submit campaign</Button></div>{preview&&<pre className="mt-4 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-emerald-200">{JSON.stringify(preview,null,2)}</pre>}
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-black">Campaigns</h2><div className="mt-3 space-y-2">{jobs.map((job)=><button key={job.job_id} onClick={()=>inspect(job)} className="w-full rounded-xl border border-slate-100 p-3 text-left hover:bg-slate-50"><div className="flex justify-between gap-2"><b className="text-sm">{job.request?.area_id || job.job_id.slice(0,8)}</b><span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold uppercase">{job.status}</span></div><p className="mt-1 text-xs text-slate-500">{job.request?.start} → {job.request?.end} · {job.total_shards} shards</p></button>)}{!jobs.length&&<p className="text-sm text-slate-500">No campaigns yet.</p>}</div></section>
    </div>
    {selected&&<section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-black">Campaign detail</h2><p className="text-xs text-slate-500">{selected.job_id} · {selected.status} · {selected.actual_bytes} bytes</p></div><div className="flex gap-2"><Button variant="outline" disabled={busy} onClick={()=>manage("retry")}><RotateCcw className="mr-1 h-4 w-4"/>Retry failed</Button><Button variant="outline" disabled={busy} onClick={()=>manage("cancel")}><Ban className="mr-1 h-4 w-4"/>Cancel</Button></div></div><div className="mt-4 overflow-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-slate-500"><th className="p-2">Source</th><th className="p-2">Window</th><th className="p-2">State</th><th className="p-2">Attempts</th><th className="p-2">Bytes</th><th className="p-2">Error</th></tr></thead><tbody>{shards.map((shard)=><tr key={shard.shard_id} className="border-b border-slate-50"><td className="p-2">{shard.spec?.source}</td><td className="p-2">{shard.spec?.start} → {shard.spec?.end}</td><td className="p-2">{shard.state}</td><td className="p-2">{shard.attempts}</td><td className="p-2">{shard.bytes}</td><td className="p-2 text-rose-600">{shard.error_message || "—"}</td></tr>)}</tbody></table></div></section>}
  </div>;
}
