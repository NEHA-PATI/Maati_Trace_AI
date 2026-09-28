import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Check, FileText, MapPin, RefreshCw, ShieldCheck, UserRound, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { decideFpoRelationship, getFpoRelationships } from "@/lib/api/fpo";

const tabs = [
  ["PENDING_FPO_ACCEPTANCE", "Needs review"],
  ["ACTIVE", "Connected"],
  ["REJECTED", "Declined"],
  ["ALL", "All requests"],
];
const readable = (value) => String(value || "Not provided").replaceAll("_", " ");
const date = (value) => value ? new Date(value).toLocaleString() : "Not recorded";

function Detail({ title, children }) {
  return <div className="min-w-0 rounded-xl bg-slate-50 px-3 py-2.5"><p className="text-[10px] font-black uppercase tracking-wide text-slate-400">{title}</p><p className="mt-1 break-words text-sm font-semibold text-slate-800">{children || "Not provided"}</p></div>;
}

function BoundaryPreview({ value }) {
  const geometry = useMemo(() => {
    if (!value) return null;
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      return parsed?.type === "Feature" ? parsed.geometry : parsed;
    } catch {
      return null;
    }
  }, [value]);
  const paths = useMemo(() => {
    if (!geometry || !["Polygon", "MultiPolygon"].includes(geometry.type) || !Array.isArray(geometry.coordinates)) return [];
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    const rings = polygons.flatMap((polygon) => polygon.slice(0, 1));
    const points = rings.flat().filter((point) => Array.isArray(point) && point.length >= 2).map(([x, y]) => [Number(x), Number(y)]).filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
    if (!points.length) return [];
    const xs = points.map(([x]) => x); const ys = points.map(([, y]) => y);
    const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
    const scale = Math.min(270 / (maxX - minX || 1), 140 / (maxY - minY || 1));
    return rings.map((ring) => ring.map(([x, y]) => `${15 + (Number(x) - minX) * scale},${155 - (Number(y) - minY) * scale}`).join(" "));
  }, [geometry]);
  return <div className="overflow-hidden rounded-xl border border-slate-200 bg-[#f1f5ed]">
    {paths.length ? <svg viewBox="0 0 300 170" role="img" aria-label="Shared farm boundary preview" className="h-36 w-full"><rect width="300" height="170" fill="#eef4e8" />{paths.map((points, index) => <polygon key={index} points={points} fill="#72b77b66" stroke="#167447" strokeWidth="2.5" strokeLinejoin="round" />)}</svg> : <div className="grid h-24 place-items-center text-xs font-semibold text-slate-500">{value ? "Boundary data is not a supported GeoJSON polygon" : "No farm boundary recorded"}</div>}
  </div>;
}

export default function FpoRelationshipsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState("PENDING_FPO_ACCEPTANCE");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState("");
  const [decisionTarget, setDecisionTarget] = useState(null);
  const [decision, setDecision] = useState("");
  const [note, setNote] = useState("");

  async function load() {
    setLoading(true);
    try {
      const result = await getFpoRelationships();
      setItems(Array.isArray(result) ? result : result?.items || []);
      setError("");
    } catch (requestError) {
      setError(requestError?.message || "Unable to load farm requests.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  const counts = useMemo(() => Object.fromEntries(tabs.map(([key]) => [key, key === "ALL" ? items.length : items.filter((item) => item.status === key).length])), [items]);
  const visible = useMemo(() => tab === "ALL" ? items : items.filter((item) => item.status === tab), [items, tab]);

  async function submitDecision() {
    if (!decisionTarget || !decision) return;
    setWorking(decisionTarget.relationship_id);
    try {
      await decideFpoRelationship(decisionTarget.relationship_id, decision, note);
      setDecisionTarget(null);
      setDecision("");
      setNote("");
      await load();
    } catch (requestError) {
      setError(requestError?.message || "The farm relationship decision could not be saved.");
    } finally {
      setWorking("");
    }
  }

  return <div className="mx-auto max-w-6xl space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-xs font-black uppercase tracking-[0.18em] text-emerald-700">Farm-level access control</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Farm connection requests</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Review the farmer and the specific farm shared with your FPO. An active relationship grants access only to that farm and only within the consented scopes.</p>
      </div>
      <Button variant="outline" onClick={load} disabled={loading}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />Refresh</Button>
    </header>
    {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div> : null}
    <section className="rounded-2xl border border-slate-200 bg-white p-2 shadow-sm" aria-label="Relationship status filters">
      <div className="flex gap-2 overflow-x-auto">{tabs.map(([key, title]) => <button key={key} type="button" onClick={() => setTab(key)} className={`shrink-0 rounded-xl px-4 py-3 text-sm font-bold ${tab === key ? "bg-emerald-800 text-white" : "text-slate-600 hover:bg-slate-100"}`}>{title}<span className={`ml-2 rounded-full px-2 py-0.5 text-xs ${tab === key ? "bg-white/20" : "bg-slate-100"}`}>{counts[key] || 0}</span></button>)}</div>
    </section>
    {loading ? <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">Loading farm requests…</div> : visible.length ? <div className="space-y-4">{visible.map((item) => {
      const pending = item.status === "PENDING_FPO_ACCEPTANCE";
      const city = [item.farm_block_name || item.block_name, item.farm_district_name || item.district_name, item.farm_state_name || item.state_name].filter(Boolean).join(", ");
      return <article key={item.relationship_id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-emerald-800"><UserRound className="h-5 w-5" /></span><div><h2 className="font-black text-slate-950">{item.full_name || "Farmer"}</h2><p className="mt-0.5 text-xs text-slate-500">{item.email_masked || "Email hidden"} · {item.phone_masked || "Phone hidden"}</p></div></div>
          <span className={`rounded-full px-3 py-1.5 text-[11px] font-black uppercase ${pending ? "bg-amber-50 text-amber-800" : item.status === "ACTIVE" ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{readable(item.status)}</span>
        </div>
        <div className="grid gap-5 p-5 lg:grid-cols-[1fr_300px]">
          <div className="space-y-4">
            <div><p className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500"><MapPin className="h-4 w-4" />Shared farm</p><h3 className="mt-1 text-lg font-black text-slate-950">{item.farm_name || "Farm name unavailable"}</h3><p className="mt-1 text-sm text-slate-600">{item.farm_id ? `Farm ID ${item.farm_id}` : "Farm ID unavailable"}</p></div>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
              <Detail title="Area">{item.area_acres != null ? `${item.area_acres} acres` : null}</Detail><Detail title="Village / block">{[item.village_name, item.farm_block_name || item.block_name].filter(Boolean).join(" / ")}</Detail><Detail title="District / state">{city || null}</Detail><Detail title="Active crop">{item.crop_name || item.crop_code}</Detail><Detail title="Farm status">{item.farm_is_active ? "Active" : "Inactive / unavailable"}</Detail><Detail title="Boundary">{item.polygon_geojson ? "Boundary available" : "No boundary recorded"}</Detail><Detail title="Land record">{item.survey_number ? "Record reference available" : "No land-record reference"}</Detail><Detail title="Request received">{date(item.created_at)}</Detail><Detail title="Consent recorded">{date(item.consent_captured_at || item.farmer_consented_at)}</Detail>
            </div>
            <div><p className="mb-2 text-[10px] font-black uppercase tracking-wide text-slate-400">Farm boundary preview</p><BoundaryPreview value={item.polygon_geojson} /></div>
            <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4"><div className="flex items-center gap-2 text-sm font-black text-emerald-950"><ShieldCheck className="h-4 w-4" />Consent and permitted access</div><div className="mt-2 grid gap-2 text-sm text-slate-700 sm:grid-cols-2"><p><b>Policy:</b> {item.policy_code ? `${item.policy_code} v${item.policy_version}` : "Not available"}</p><p><b>Language:</b> {item.language_code || "Not provided"}</p><p><b>Scopes:</b> {(item.scopes || []).map(readable).join(", ") || "No scopes recorded"}</p><p><b>Expiry:</b> {item.consent_expires_at ? date(item.consent_expires_at) : "No expiry set"}</p></div></div>
            <div className="flex items-start gap-2 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600"><FileText className="mt-0.5 h-4 w-4 shrink-0" /><p>Farmer documents are not exposed here because no secure farmer-document review source is configured. Only document availability metadata, when provided, should be shown.</p></div>
          </div>
          <aside className="flex flex-col gap-2 lg:border-l lg:border-slate-100 lg:pl-5">
            {item.status === "ACTIVE" ? <Button variant="outline" onClick={() => navigate(`/fpo/farmers/${item.farmer_id}/farms/${item.farm_id}/intelligence`)} disabled={!item.farm_id}>Open land intelligence</Button> : <Button variant="outline" disabled>Land intelligence unlocks after acceptance</Button>}
            {item.status === "ACTIVE" ? <Button variant="outline" onClick={() => navigate(`/fpo/farmers/${item.farmer_id}`)}>Open farmer profile</Button> : <Button variant="outline" disabled>Farmer profile is private until accepted</Button>}
            {pending ? <><Button onClick={() => { setDecisionTarget(item); setDecision("ACTIVE"); }} className="bg-emerald-800 hover:bg-emerald-900"><Check className="mr-2 h-4 w-4" />Accept farm request</Button><Button variant="outline" onClick={() => { setDecisionTarget(item); setDecision("REJECTED"); }} className="text-rose-700"><X className="mr-2 h-4 w-4" />Reject request</Button></> : null}
          </aside>
        </div>
      </article>;
    })}</div> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center"><p className="font-bold text-slate-800">{tab === "PENDING_FPO_ACCEPTANCE" ? "No farm requests need review" : "No relationships in this view"}</p><p className="mt-1 text-sm text-slate-500">New farmer requests will appear here as soon as they are submitted.</p></div>}
    {decisionTarget ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4"><section role="dialog" aria-modal="true" aria-labelledby="relationship-decision-title" className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl"><p className="text-xs font-black uppercase tracking-widest text-emerald-700">Confirm decision</p><h2 id="relationship-decision-title" className="mt-2 text-xl font-black text-slate-950">{decision === "ACTIVE" ? "Accept this farm connection?" : "Reject this request?"}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{decisionTarget.farm_name || "This farm"} · {decisionTarget.full_name || "Farmer"}. {decision === "ACTIVE" ? "Your FPO will receive access only to this farm within the farmer's recorded consent scopes." : "The farmer will see the request as declined and can choose another FPO."}</p><label className="mt-4 block text-sm font-bold text-slate-700">Decision note <span className="font-normal text-slate-400">(optional)</span><textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength={1000} rows={3} className="mt-2 w-full rounded-xl border border-slate-300 p-3 font-normal outline-none focus:border-emerald-700" placeholder="Add context for your records" /></label><div className="mt-5 flex justify-end gap-2"><Button variant="outline" onClick={() => setDecisionTarget(null)}>Cancel</Button><Button onClick={submitDecision} disabled={Boolean(working)} className={decision === "ACTIVE" ? "bg-emerald-800" : "bg-rose-700"}>{working ? "Saving…" : decision === "ACTIVE" ? "Confirm acceptance" : "Confirm rejection"}</Button></div></section></div> : null}
  </div>;
}
