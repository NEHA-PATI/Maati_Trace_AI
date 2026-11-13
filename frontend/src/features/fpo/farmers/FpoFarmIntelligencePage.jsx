import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ArrowLeft, ChevronRight, MapPin, TrendingDown, TrendingUp, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import LandGridMap from "@/components/ui-custom/LandGridMap";
import { CALCULATED_METRICS, interpretCalculatedMetric } from "@/features/land-intelligence/calculatedMetrics";
import { getFpoFarmIntelligence } from "../api/fpoFarmerApi";
import "./fpoFarmIntelligence.css";

const formatDate = (value) => value ? new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "Not available";
const locationOf = (farm) => [farm.village_name, farm.block_name, farm.district_name, farm.state_name].filter(Boolean).join(", ") || "Location not recorded";
const scoreOf = (row) => row?.score ?? row?.value ?? null;
const recommendationFor = (key) => ({ water_stress: "Schedule an irrigation inspection for this farm.", heat_stress: "Check field moisture and heat exposure during the next field visit.", waterlogging_risk: "Inspect drainage and standing-water areas.", nutrient_stress_risk: "Arrange a field and soil review before applying inputs.", erosion_risk: "Inspect slopes, drainage paths, and exposed soil.", growth_anomaly: "Schedule a field inspection to confirm the growth change." }[key] || "Review the crop condition during the next field visit.");

const tones = {
  healthy: { label: "Healthy", bg: "#E3F3EB", fg: "#0A6444", bar: "#1E9E6F" },
  fair: { label: "Fair", bg: "#ECF2D2", fg: "#485A10", bar: "#8AA82A" },
  watch: { label: "Watch", bg: "#FAEDC4", fg: "#74530A", bar: "#D9A400" },
  attention: { label: "Attention", bg: "#FCE0CC", fg: "#9A3A0B", bar: "#E0661F" },
};

function toneFor(metric, value) {
  if (value === null) return { label: "No data", bg: "#EEF1ED", fg: "#64706A", bar: "#AAB4AC" };
  const status = interpretCalculatedMetric(metric.key, value).status;
  if (["critical", "high", "attention", "poor"].includes(status)) return tones.attention;
  if (["watch", "fair"].includes(status)) return tones.watch;
  return tones.healthy;
}

function SignalCard({ metric, row, index, onClick }) {
  const raw = scoreOf(row);
  const value = raw === null || raw === undefined ? null : Math.max(0, Math.min(100, Number(raw)));
  const tone = toneFor(metric, value);
  return <button type="button" className="fpo-signal-card" style={{ "--card-delay": `${160 + index * 60}ms`, "--signal-score": `${value ?? 0}%`, "--signal-bar": tone.bar }} onClick={onClick}>
    <span className="fpo-signal-title"><span>{metric.name}</span><ChevronRight className="fpo-chevron" /></span>
    <span className="fpo-signal-score"><span><strong>{value === null ? "-" : Math.round(value)}</strong><small>/100</small></span><em style={{ background: tone.bg, color: tone.fg }}>{tone.label}</em></span>
    <span className="fpo-signal-progress" aria-hidden="true"><span /></span>
  </button>;
}

function HistoryModal({ metric, currentRow, history, onClose }) {
  const interpretation = interpretCalculatedMetric(metric.key, scoreOf(currentRow));
  const points = useMemo(() => history.filter((row) => row.prediction_key === metric.key && scoreOf(row) !== null).sort((a, b) => new Date(a.result_date) - new Date(b.result_date)), [history, metric.key]);
  const first = points[0] ? Number(scoreOf(points[0])) : null;
  const last = points.at(-1) ? Number(scoreOf(points.at(-1))) : null;
  const trend = first !== null && last !== null && last !== first ? last > first ? "Increasing" : "Decreasing" : "Stable";
  useEffect(() => { const onKey = (event) => event.key === "Escape" && onClose(); window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey); }, [onClose]);
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[.16em] text-emerald-700">Parameter history</p><h2 className="mt-2 text-2xl font-black text-slate-950">{metric.name}</h2></div><button type="button" onClick={onClose} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100"><X className="h-5 w-5" /></button></div><div className="mt-5 rounded-2xl border border-orange-200 bg-orange-50 p-4"><div className="flex items-center justify-between"><strong className="text-3xl text-slate-950">{scoreOf(currentRow) === null ? "-" : Math.round(Number(scoreOf(currentRow)))}/100</strong><span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-700">{interpretation.label}</span></div><p className="mt-3 text-sm text-slate-700">{interpretation.paragraph || interpretation.signalMeaning}</p></div><div className="mt-6 flex items-center justify-between"><h3 className="font-black text-slate-950">Historical movement</h3>{points.length > 1 && <span className="flex items-center gap-1 text-xs font-bold text-slate-500">{trend === "Increasing" ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}{trend}</span>}</div>{points.length < 2 ? <p className="mt-4 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">Historical data is not available yet.</p> : <div className="mt-4 space-y-3">{points.slice().reverse().map((point) => <div key={`${point.result_date}-${point.prediction_key}`} className="flex items-center gap-3"><span className="w-24 text-xs text-slate-500">{formatDate(point.result_date)}</span><div className="h-8 flex-1 rounded-lg bg-slate-100"><div className="h-full rounded-lg bg-emerald-500" style={{ width: `${Number(scoreOf(point))}%` }} /></div><strong className="w-10 text-right text-sm">{Math.round(Number(scoreOf(point)))}</strong></div>)}</div>}</div></div>;
}

export default function FpoFarmIntelligencePage() {
  const { farmerId, farmId } = useParams();
  const [selectedMetric, setSelectedMetric] = useState(null);
  const query = useQuery({ queryKey: ["fpo-farm-intelligence", farmerId, farmId], queryFn: () => getFpoFarmIntelligence(farmerId, farmId), enabled: Boolean(farmerId && farmId) });
  if (query.isLoading) return <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading farm intelligence...</div>;
  if (query.isError) return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">Farm intelligence is unavailable or this farm is outside the active consent scope.</div>;
  const payload = query.data || {}; const farm = payload.farm || {}; const data = payload.data || {}; const calculations = data.calculations?.items || []; const history = data.calculation_history?.items || []; const gridValues = data.grid_values?.items || []; const gridCalculations = data.grid_calculations?.items || [];
  const gridCells = gridValues.map((cell) => ({ ...cell, ...(gridCalculations.find((item) => String(item.grid_cell_id) === String(cell.grid_cell_id)) || {}) }));
  const rows = CALCULATED_METRICS.map((metric) => ({ metric, row: calculations.find((item) => item.prediction_key === metric.key) }));
  const summary = rows.reduce((result, item) => { const value = scoreOf(item.row); const tone = toneFor(item.metric, value === null ? null : Number(value)); const key = Object.keys(tones).find((name) => tones[name].label === tone.label) || "attention"; result[key] += 1; return result; }, { healthy: 0, fair: 0, watch: 0, attention: 0 });
  const priority = rows.find((item) => { const value = scoreOf(item.row); const status = interpretCalculatedMetric(item.metric.key, value).status; return ["critical", "high", "attention", "poor", "watch"].includes(status); }) || rows[0];
  const selected = selectedMetric ? rows.find((item) => item.metric.key === selectedMetric) : null;
  return <div className="fpo-intelligence-page"><div className="fpo-intelligence-shell"><div className="fpo-intelligence-header"><div><a href="/fpo/monitoring" className="mb-3 inline-flex items-center gap-2 text-sm font-bold text-emerald-700"><ArrowLeft className="h-4 w-4" />Back to monitoring</a><h1>Farm intelligence</h1><p>Select a parameter to review its historical movement.</p></div><div className="fpo-summary-pills">{Object.entries(summary).map(([key, count]) => <span key={key} style={{ background: tones[key].bg, color: tones[key].fg }}><strong>{count}</strong> {tones[key].label}</span>)}</div></div>
    <div className="fpo-priority"><div><span className="fpo-priority-label"><i />Priority issue</span><h2>{priority?.metric.name || "No priority issue"}</h2><p>Suggested action: {priority ? recommendationFor(priority.metric.key) : "Continue monitoring the farm."}</p></div><div className="fpo-priority-score"><strong>{priority?.row && scoreOf(priority.row) !== null ? Math.round(Number(scoreOf(priority.row))) : "-"}<small>/100</small></strong><span>Attention</span><b><i style={{ width: `${priority?.row && scoreOf(priority.row) !== null ? Number(scoreOf(priority.row)) : 0}%` }} /></b></div></div>
    <div className="fpo-signal-grid">{rows.map(({ metric, row }, index) => <SignalCard key={metric.key} metric={metric} row={row} index={index} onClick={() => setSelectedMetric(metric.key)} />)}</div>
    <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-black text-slate-950">Farm map</h2><p className="mt-1 text-sm text-slate-500">Boundary and selected intelligence parameter.</p></div></div><div className="mt-4"><LandGridMap farm={farm} gridCells={gridCells} selectedParameter={selectedMetric || CALCULATED_METRICS[0].key} /></div></div></div>{selected && <HistoryModal metric={selected.metric} currentRow={selected.row} history={history} onClose={() => setSelectedMetric(null)} />}</div>;
}
