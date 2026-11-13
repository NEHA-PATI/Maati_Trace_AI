import { useMemo, useState } from "react";
import { Download, Droplets, Leaf, Mountain, Thermometer, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import FpoFeatureGate from "../access/FpoFeatureGate";
import { getFpoFarmMonitoring } from "../api/fpoFarmerApi";
import { CALCULATED_METRICS, interpretCalculatedMetric } from "@/features/land-intelligence/calculatedMetrics";
import reportFarmBackground from "@/assets/fpo/report-farm-background.png";

const buckets = [
  { title: "Crop Health & Growth", icon: Leaf, keys: ["crop_condition", "growth_condition", "growth_anomaly"], color: "#1E9E6F", overlay: "rgba(236,253,245,.90)" },
  { title: "Water & Moisture", icon: Droplets, keys: ["water_stress", "moisture_condition", "waterlogging_risk"], color: "#2878B8", overlay: "rgba(239,246,255,.90)" },
  { title: "Soil & Land Health", icon: Mountain, keys: ["soil_condition", "nutrient_stress_risk", "erosion_risk"], color: "#A47712", overlay: "rgba(255,251,235,.90)" },
  { title: "Environmental Stress", icon: Thermometer, keys: ["heat_stress"], color: "#C6522E", overlay: "rgba(255,241,242,.90)" },
];

const score = (row) => Number.isFinite(Number(row?.score)) ? Math.max(0, Math.min(10, Number(row.score) / 10)) : null;

function MetricLine({ metric, row, selected, onSelect }) {
  const value = score(row);
  const interpretation = interpretCalculatedMetric(metric.key, value === null ? null : value * 10);
  const status = row?.status_label || (value === null ? "No data" : value >= 7 ? "Healthy" : value >= 4 ? "Watch" : "Needs attention");
  const statusStyle = value === null ? "bg-slate-100 text-slate-500" : value >= 7 ? "bg-emerald-100 text-emerald-700" : value >= 4 ? "bg-amber-100 text-amber-700" : "bg-orange-100 text-orange-700";
  return <button type="button" onClick={onSelect} aria-pressed={selected} className={`group w-full rounded-2xl border bg-white/90 p-4 text-left shadow-[0_1px_2px_rgba(27,36,48,.04)] transition hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-lg ${selected ? "border-slate-950 ring-2 ring-slate-950/10" : "border-[#E1E4DC]"}`}>
    <span className="flex items-start justify-between gap-3"><span className="text-sm font-semibold leading-5 text-slate-900">{metric.name}</span><ChevronRight className="h-4 w-4 shrink-0 text-slate-500 transition group-hover:translate-x-1" /></span>
    <span className="mt-3 flex items-end justify-between gap-3"><span><span className="text-3xl font-semibold leading-none text-slate-950">{value === null ? "-" : value.toFixed(1)}</span><span className="ml-1 text-sm text-slate-500">/10</span></span><span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${statusStyle}`}>{String(status).replaceAll("_", " ")}</span></span>
    <span className="mt-3 block h-2 overflow-hidden rounded-full bg-slate-200"><span className="block h-full rounded-full transition-all" style={{ width: `${value === null ? 0 : value * 10}%`, background: value === null ? "#CBD5E1" : interpretation.color || "#1E9E6F" }} /></span>
    <span className="mt-3 block text-xs leading-5 text-slate-600">{value === null ? "No current score is available for this parameter." : interpretation.paragraph || interpretation.signalMeaning || "Review this signal in Monitoring."}</span>
  </button>;
}

export default function FpoReportsPage() {
  const [crop, setCrop] = useState("");
  const [location, setLocation] = useState("");
  const [selected, setSelected] = useState(null);
  const farmsQuery = useQuery({ queryKey: ["fpo-report-farms"], queryFn: () => getFpoFarmMonitoring(), staleTime: 30000 });
  const farms = farmsQuery.data?.items || [];
  const crops = [...new Set(farms.map((f) => f.crop_name || f.crop_code).filter(Boolean))].sort();
  const locations = [...new Set(farms.map((f) => f.village_name || f.block_name).filter(Boolean))].sort();
  const filtered = farms.filter((f) => (!crop || (f.crop_name || f.crop_code) === crop) && (!location || (f.village_name || f.block_name) === location));
  const rows = useMemo(() => CALCULATED_METRICS.map((metric) => ({ metric, average: (() => { const values = filtered.map((f) => score((f.predictions || []).find((p) => p.prediction_key === metric.key))).filter((v) => v !== null); return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null; })() })), [filtered]);
  const summary = rows.reduce((acc, row) => { const value = row.average; acc[value === null ? "none" : value >= 7 ? "healthy" : value >= 4 ? "watch" : "attention"] += 1; return acc; }, { healthy: 0, watch: 0, attention: 0, none: 0 });
  const download = () => { const csv = [["Bucket", "Parameter", "Average score / 10"], ...buckets.flatMap((bucket) => bucket.keys.map((key) => { const row = rows.find((item) => item.metric.key === key); return [bucket.title, row.metric.name, row.average === null ? "" : row.average.toFixed(1)]; }))].map((r) => r.join(",")).join("\n"); const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); const a = document.createElement("a"); a.href = url; a.download = "fpo-intelligence-report.csv"; a.click(); URL.revokeObjectURL(url); };
  return <FpoFeatureGate feature="BASIC_REPORTS" fallback={<div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">Portfolio reports are not enabled for this organization.</div>}><div className="space-y-7 pb-10"><header className="flex flex-wrap items-end justify-between gap-5"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">FPO Reports</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Portfolio intelligence</h1><p className="mt-1 text-sm text-slate-500">A clear 10-point view across crop, water, soil, and environmental health.</p></div><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-bold text-emerald-700">{summary.healthy} healthy</span><span className="rounded-full bg-amber-100 px-3 py-1.5 text-xs font-bold text-amber-700">{summary.watch} watch</span><span className="rounded-full bg-orange-100 px-3 py-1.5 text-xs font-bold text-orange-700">{summary.attention} attention</span><button type="button" onClick={download} className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white"><Download className="h-4 w-4" />Export</button></div></header>
    <section className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4"><select value={crop} onChange={(e) => setCrop(e.target.value)} className="rounded-xl border border-slate-300 px-3 py-2 text-sm"><option value="">All crops</option>{crops.map((x) => <option key={x}>{x}</option>)}</select><select value={location} onChange={(e) => setLocation(e.target.value)} className="rounded-xl border border-slate-300 px-3 py-2 text-sm"><option value="">All villages / blocks</option>{locations.map((x) => <option key={x}>{x}</option>)}</select><span className="ml-auto text-xs font-bold text-slate-400">{filtered.length} farms included</span></section>
    {farmsQuery.isLoading ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Preparing report...</div> : <section className="grid gap-5 lg:grid-cols-2">{buckets.map((bucket) => { const Icon = bucket.icon; return <article key={bucket.title} className="relative overflow-hidden rounded-[22px] border border-[#E1E4DC] bg-cover bg-center p-5" style={{ backgroundImage: `linear-gradient(105deg, ${bucket.overlay} 0%, rgba(255,255,255,.70) 100%), url(${reportFarmBackground})` }}><div className="absolute -right-12 -top-14 h-44 w-44 rounded-full bg-white/40" /><div className="relative mb-4 flex items-center gap-3"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/90 shadow-sm"><Icon className="h-6 w-6" style={{ color: bucket.color }} /></span><div><h2 className="text-lg font-semibold text-slate-950">{bucket.title}</h2><p className="text-xs text-slate-600">Average score out of 10</p></div></div><div className="relative space-y-3">{bucket.keys.map((key) => { const row = rows.find((item) => item.metric.key === key); return row ? <MetricLine key={key} metric={row.metric} row={{ score: row.average === null ? null : row.average * 10 }} selected={selected === key} onSelect={() => setSelected(selected === key ? null : key)} /> : null; })}</div></article>; })}</section>}
    <p className="rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-600">Scores summarize the latest available farm intelligence in the selected portfolio. Select a parameter for a focused view, or use Monitoring to inspect the farm boundary and historical graph.</p></div></FpoFeatureGate>;
}
