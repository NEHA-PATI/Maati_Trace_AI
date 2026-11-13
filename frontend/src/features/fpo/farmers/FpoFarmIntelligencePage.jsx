import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ArrowLeft, ChevronRight, MapPin, TrendingDown, TrendingUp, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import LandGridMap from "@/components/ui-custom/LandGridMap";
import { CALCULATED_METRICS, calculatedValueFromCell, interpretCalculatedMetric } from "@/features/land-intelligence/calculatedMetrics";
import { getFpoFarmIntelligence } from "../api/fpoFarmerApi";
import "./fpoFarmIntelligence.css";

const formatDate = (value) => value ? new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "Not available";
const scoreOf = (row, metric = null) => metric ? calculatedValueFromCell(row, metric.key) : row?.score ?? row?.value ?? null;
const recommendationFor = (key) => ({ water_stress: "Schedule an irrigation inspection for this farm.", heat_stress: "Check field moisture and heat exposure during the next field visit.", waterlogging_risk: "Inspect drainage and standing-water areas.", nutrient_stress_risk: "Arrange a field and soil review before applying inputs.", erosion_risk: "Inspect slopes, drainage paths, and exposed soil.", growth_anomaly: "Schedule a field inspection to confirm the growth change." }[key] || "Review the crop condition during the next field visit.");

const statusTones = {
  normal: { label: "Normal", bg: "#E3F3EB", fg: "#0A6444" },
  fair: { label: "Fair", bg: "#ECF2D2", fg: "#485A10" },
  watch: { label: "Watch", bg: "#FAEDC4", fg: "#74530A" },
  attention: { label: "Needs attention", bg: "#FCE0CC", fg: "#9A3A0B" },
  critical: { label: "Critical", bg: "#FDE2E2", fg: "#B42318" },
  no_data: { label: "No data", bg: "#EEF1ED", fg: "#64706A" },
};

function overallStatusFor(metric, row) {
  const value = scoreOf(row, metric);
  if (!row || value === null || value === undefined) return "no_data";
  const stored = String(row?.status_label || "").trim().toLowerCase();
  const status = ["normal", "good", "fair", "watch", "attention", "high", "poor", "critical"].includes(stored)
    ? stored
    : interpretCalculatedMetric(metric.key, value).status;
  if (["normal", "good"].includes(status)) return "normal";
  if (status === "fair") return "fair";
  if (status === "watch") return "watch";
  if (status === "critical") return "critical";
  return "attention";
}

function toneFor(metric, value) {
  const result = interpretCalculatedMetric(metric.key, value);
  return { label: result.label, color: result.color, surfaceColor: result.surfaceColor, badgeClass: result.badgeClass };
}

const prioritySeverity = { critical: 5, high: 4, poor: 4, attention: 3, watch: 2 };

function priorityFor(rows) {
  const ranked = rows
    .map((item) => {
      const value = scoreOf(item.row, item.metric);
      const result = interpretCalculatedMetric(item.metric.key, value);
      const urgency = item.metric.direction === "risk" ? Number(value) : 100 - Number(value);
      return { ...item, result, severity: prioritySeverity[result.status] || 0, urgency };
    })
    .filter((item) => Number.isFinite(item.urgency) && item.severity > 0)
    .sort((a, b) => b.severity - a.severity || b.urgency - a.urgency);
  return ranked[0] || null;
}

function SignalCard({ metric, row, index, onClick }) {
  const raw = scoreOf(row, metric);
  const value = raw === null || raw === undefined ? null : Math.max(0, Math.min(100, Number(raw)));
  const tone = toneFor(metric, value);
  return <button type="button" className="fpo-signal-card" style={{ "--card-delay": `${160 + index * 60}ms`, "--signal-score": `${value ?? 0}%`, "--signal-bar": tone.color, backgroundColor: tone.surfaceColor }} onClick={onClick}>
    <span className="fpo-signal-title"><span>{metric.name}</span><ChevronRight className="fpo-chevron" /></span>
    <span className="fpo-signal-score"><span><strong>{value === null ? "-" : Math.round(value)}</strong><small>/100</small></span><em className={tone.badgeClass}>{tone.label}</em></span>
    <span className="fpo-signal-progress" aria-hidden="true"><span /></span>
  </button>;
}

function HistoryModal({ metric, currentRow, history, onClose }) {
  const interpretation = interpretCalculatedMetric(metric.key, scoreOf(currentRow, metric));
  const points = useMemo(() => history.filter((row) => row.prediction_key === metric.key && scoreOf(row, metric) !== null).sort((a, b) => new Date(a.result_date) - new Date(b.result_date)), [history, metric]);
  const first = points[0] ? Number(scoreOf(points[0], metric)) : null;
  const last = points.at(-1) ? Number(scoreOf(points.at(-1), metric)) : null;
  const trend = first !== null && last !== null && last !== first ? last > first ? "Increasing" : "Decreasing" : "Stable";
  useEffect(() => { const onKey = (event) => event.key === "Escape" && onClose(); window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey); }, [onClose]);
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-3xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-[.16em] text-emerald-700">Parameter history</p><h2 className="mt-2 text-2xl font-black text-slate-950">{metric.name}</h2></div><button type="button" onClick={onClose} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100"><X className="h-5 w-5" /></button></div><div className={`mt-5 rounded-2xl border p-4 ${interpretation.surfaceClass}`}><div className="flex items-center justify-between"><strong className="text-3xl text-slate-950">{scoreOf(currentRow, metric) === null ? "-" : Math.round(Number(scoreOf(currentRow, metric)))}/100</strong><span className={`rounded-full border px-3 py-1 text-xs font-bold ${interpretation.badgeClass}`}>{interpretation.label}</span></div><p className="mt-3 text-sm text-slate-700">{interpretation.paragraph || interpretation.signalMeaning}</p></div><div className="mt-6 flex items-center justify-between"><h3 className="font-black text-slate-950">Historical movement</h3>{points.length > 1 && <span className="flex items-center gap-1 text-xs font-bold text-slate-500">{trend === "Increasing" ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}{trend}</span>}</div>{points.length < 2 ? <p className="mt-4 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">Historical data is not available yet.</p> : <div className="mt-4 space-y-3">{points.slice().reverse().map((point) => { const pointScore = Number(scoreOf(point, metric)); const pointColor = interpretCalculatedMetric(metric.key, pointScore).color; return <div key={`${point.result_date}-${point.prediction_key}`} className="flex items-center gap-3"><span className="w-24 text-xs text-slate-500">{formatDate(point.result_date)}</span><div className="h-8 flex-1 rounded-lg bg-slate-100"><div className="h-full rounded-lg" style={{ width: `${pointScore}%`, backgroundColor: pointColor }} /></div><strong className="w-10 text-right text-sm">{Math.round(pointScore)}</strong></div>; })}</div>}</div></div>;
}

export default function FpoFarmIntelligencePage() {
  const { farmerId, farmId } = useParams();
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [selectedGridCell, setSelectedGridCell] = useState(null);
  const query = useQuery({ queryKey: ["fpo-farm-intelligence", farmerId, farmId], queryFn: () => getFpoFarmIntelligence(farmerId, farmId), enabled: Boolean(farmerId && farmId) });
  if (query.isLoading) return <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading farm intelligence...</div>;
  if (query.isError) return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">Farm intelligence is unavailable or this farm is outside the active consent scope.</div>;
  const payload = query.data || {}; const farm = payload.farm || {}; const data = payload.data || {}; const calculations = Array.isArray(data.calculations?.items) ? data.calculations.items : []; const history = Array.isArray(data.calculation_history?.items) ? data.calculation_history.items : []; const gridValues = Array.isArray(data.grid_values?.items) ? data.grid_values.items : []; const gridCalculations = Array.isArray(data.grid_calculations?.items) ? data.grid_calculations.items : [];
  const gridCells = gridValues.map((cell) => ({ ...cell, ...(gridCalculations.find((item) => String(item.grid_cell_id) === String(cell.grid_cell_id)) || {}) }));
  const rows = CALCULATED_METRICS.map((metric) => ({ metric, row: calculations.find((item) => item.prediction_key === metric.key) }));
  const summary = rows.reduce((result, item) => { result[overallStatusFor(item.metric, item.row)] += 1; return result; }, { normal: 0, fair: 0, watch: 0, attention: 0, critical: 0, no_data: 0 });
  const selectedGridCellIndex = selectedGridCell ? gridCells.findIndex((cell) => String(cell.grid_cell_id) === String(selectedGridCell.grid_cell_id)) : -1;
  const selectedGridReadings = selectedGridCell
    ? CALCULATED_METRICS.map((metric) => {
      const value = calculatedValueFromCell(selectedGridCell, metric.key);
      return { metric, value, result: interpretCalculatedMetric(metric.key, value) };
    })
    : [];
  const priority = priorityFor(rows);
  const priorityResult = priority?.result || null;
  const selected = selectedMetric ? rows.find((item) => item.metric.key === selectedMetric) : null;
  return <div className="fpo-intelligence-page"><div className="fpo-intelligence-shell"><div className="fpo-intelligence-header"><div><a href="/fpo/monitoring" className="mb-3 inline-flex items-center gap-2 text-sm font-bold text-emerald-700"><ArrowLeft className="h-4 w-4" />Back to monitoring</a><h1>Farm intelligence</h1><p>Select a parameter to review its historical movement.</p></div><div className="fpo-summary-pills">{Object.entries(summary).map(([key, count]) => <span key={key} style={{ background: statusTones[key].bg, color: statusTones[key].fg }}><strong>{count}</strong> {statusTones[key].label}</span>)}</div></div>
    <div className="fpo-priority" style={priorityResult ? { backgroundColor: priorityResult.surfaceColor, borderColor: priorityResult.color } : undefined}><div><span className="fpo-priority-label" style={priorityResult ? { color: priorityResult.color } : undefined}><i style={priorityResult ? { background: priorityResult.color } : undefined} />Priority issue</span><h2>{priority?.metric.name || "No priority issue"}</h2><p>Suggested action: {priority ? recommendationFor(priority.metric.key) : "Continue monitoring the farm."}</p></div><div className="fpo-priority-score"><strong>{priority?.row && scoreOf(priority.row, priority.metric) !== null ? Math.round(Number(scoreOf(priority.row, priority.metric))) : "-"}<small>/100</small></strong><span style={priorityResult ? { background: priorityResult.surfaceColor, color: priorityResult.color } : undefined}>{priorityResult?.label || "No data"}</span><b style={priorityResult ? { background: `${priorityResult.color}33` } : undefined}><i style={{ width: `${priority?.row && scoreOf(priority.row, priority.metric) !== null ? Number(scoreOf(priority.row, priority.metric)) : 0}%`, background: priorityResult?.color }} /></b></div></div>
    <div className="fpo-signal-grid">{rows.map(({ metric, row }, index) => <SignalCard key={metric.key} metric={metric} row={row} index={index} onClick={() => setSelectedMetric(metric.key)} />)}</div>
    <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-black text-slate-950">Farm map</h2><p className="mt-1 text-sm text-slate-500">Boundary and selected intelligence parameter. Click a grid cell to inspect its readings.</p></div></div><div className="mt-4"><LandGridMap farm={farm} gridCells={gridCells} selectedParameter={selectedMetric || CALCULATED_METRICS[0].key} onGridCellClick={setSelectedGridCell} selectedGridCellId={selectedGridCell?.grid_cell_id} maxZoom={19} /></div></div></div>{selectedGridCell && <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && setSelectedGridCell(null)}><div className="max-h-[88vh] w-full max-w-4xl overflow-y-auto rounded-3xl bg-white p-5 shadow-2xl sm:p-6"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-black uppercase tracking-[.14em] text-emerald-700">Selected land cell</p><h3 className="mt-1 text-xl font-black text-slate-950">{selectedGridCellIndex >= 0 ? `Cell ${selectedGridCellIndex + 1} of ${gridCells.length}` : "Selected cell"}</h3></div><button type="button" onClick={() => setSelectedGridCell(null)} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100" aria-label="Close selected cell details"><X className="h-5 w-5" /></button></div><div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">{selectedGridReadings.map(({ metric, value, result }) => <div key={metric.key} className={`rounded-xl border p-3 ${result.surfaceClass}`}><div className="flex items-start justify-between gap-2"><span className="text-xs font-bold text-slate-800">{metric.name}</span><span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-semibold ${result.className}`}>{value === null ? "No data" : result.label}</span></div><div className={`mt-2 text-xl font-black ${result.textClass}`}>{value === null ? "-" : `${Math.round(Number(value))}/100`}</div><p className="mt-1 text-[11px] leading-snug text-slate-600">{result.paragraph || result.signalMeaning}</p></div>)}</div></div></div>}{selected && <HistoryModal metric={selected.metric} currentRow={selected.row} history={history} onClose={() => setSelectedMetric(null)} />}</div>;
}
