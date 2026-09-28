import { useQuery } from "@tanstack/react-query";
import FpoFeatureGate from "../access/FpoFeatureGate";
import { getFpoDashboardReport } from "../api/fpoDashboardApi";

function Metric({ label, value }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-2 text-3xl font-black text-slate-950">{value ?? 0}</p></div>; }

export default function FpoReportsPage() {
  const report = useQuery({ queryKey: ["fpo-portfolio-report-page"], queryFn: getFpoDashboardReport });
  const data = report.data || {};
  const portfolio = data.portfolio || {};
  const coverage = data.coverage || {};
  return <FpoFeatureGate feature="BASIC_REPORTS" fallback={<div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">Portfolio reports are not enabled for this organization.</div>}>
    <div className="space-y-6"><div><h1 className="text-3xl font-black text-slate-950">Portfolio reports</h1><p className="mt-1 text-sm text-slate-500">A read-only summary of your active farmer and farm portfolio.</p></div>{report.isLoading ? <p className="text-sm text-slate-500">Loading portfolio report...</p> : report.isError ? <p className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">Unable to load the portfolio report.</p> : <><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Active farmers" value={portfolio.active_farmer_count} /><Metric label="Pending relationships" value={portfolio.pending_farmer_count} /><Metric label="Active farms" value={portfolio.active_farm_count} /><Metric label="Registered area (acres)" value={portfolio.registered_area_acres} /></div><section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-black text-slate-950">Coverage and freshness</h2><p className="mt-2 text-sm text-slate-600">Districts: {coverage.district_count || 0} · Blocks: {coverage.block_count || 0} · Villages: {coverage.village_count || 0}</p><p className="mt-2 text-sm text-slate-600">Data through: {data.data_freshness?.data_through ? new Date(data.data_freshness.data_through).toLocaleString() : "Not available"}</p><p className="mt-1 text-xs text-slate-400">Calculation version: {data.data_freshness?.calculation_version || "fpo-portfolio-v2"} · {data.data_freshness?.stale ? "Stale" : "Fresh"}</p></section></>}</div>
  </FpoFeatureGate>;
}
