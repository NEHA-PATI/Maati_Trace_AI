import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import FpoFeatureGate from "../access/FpoFeatureGate";
import { getFpoDashboardReport } from "../api/fpoDashboardApi";
import { discoverFpoFarmers } from "../api/fpoFarmerApi";

function Metric({ label, value }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-2 text-3xl font-black text-slate-950">{value ?? 0}</p></div>; }

export default function FpoMonitoringPage() {
  const report = useQuery({ queryKey: ["fpo-monitoring-report"], queryFn: getFpoDashboardReport });
  const portfolio = useQuery({ queryKey: ["fpo-monitoring-farmers"], queryFn: () => discoverFpoFarmers({ limit: 100 }) });
  const items = portfolio.data?.items || portfolio.data || [];
  const crops = useMemo(() => items.reduce((result, item) => { (item.active_crop_codes || []).forEach((crop) => { result[crop] = (result[crop] || 0) + 1; }); return result; }, {}), [items]);
  const summary = report.data || {};
  const attention = summary.attention || {};
  const freshness = summary.data_freshness || {};
  return <FpoFeatureGate feature="FARM_MAP" fallback={<div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">Farm monitoring is not enabled for this organization.</div>}>
    <div className="space-y-6"><div><h1 className="text-3xl font-black text-slate-950">Coverage and crop monitoring</h1><p className="mt-1 text-sm text-slate-500">Portfolio-level coverage, crop distribution, and farm attention signals.</p></div>{report.isLoading || portfolio.isLoading ? <p className="text-sm text-slate-500">Loading monitoring data...</p> : <><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Farmers covered" value={summary.portfolio?.active_farmer_count} /><Metric label="Farms covered" value={summary.portfolio?.active_farm_count} /><Metric label="Area (acres)" value={summary.portfolio?.registered_area_acres} /><Metric label="Open alerts" value={attention.open_alert_count} /></div><div className="grid gap-6 lg:grid-cols-2"><section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-black text-slate-950">Crop distribution</h2><div className="mt-4 space-y-3">{Object.keys(crops).length ? Object.entries(crops).sort(([, a], [, b]) => b - a).map(([crop, count]) => <div key={crop} className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3"><span className="font-semibold text-slate-700">{crop}</span><span className="font-black text-emerald-700">{count}</span></div>) : <p className="text-sm text-slate-500">No active crop observations are available through consented relationships.</p>}</div></section><section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-black text-slate-950">Farm attention</h2><div className="mt-4 space-y-3">{items.filter((item) => item.condition_status && item.condition_status !== "UNKNOWN").slice(0, 10).map((item) => <div key={item.farmer_id} className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3"><div><p className="font-semibold text-slate-800">{item.farmer_name}</p><p className="text-xs text-slate-500">{item.farm_count} farms · {item.area_acres} acres</p></div><span className="text-xs font-black uppercase text-amber-700">{item.condition_status}</span></div>)}{!items.some((item) => item.condition_status && item.condition_status !== "UNKNOWN") ? <p className="text-sm text-slate-500">No farm attention signals are currently available.</p> : null}</div></section></div><p className="text-xs text-slate-400">Data through: {freshness.data_through ? new Date(freshness.data_through).toLocaleString() : "read model not refreshed"}</p></>}</div>
  </FpoFeatureGate>;
}
