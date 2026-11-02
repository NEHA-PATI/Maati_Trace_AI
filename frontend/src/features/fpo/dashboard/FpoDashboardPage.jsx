import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, MapPinned } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import FpoFeatureGate from "@/features/fpo/access/FpoFeatureGate";
import { getFpoDashboardReport } from "@/features/fpo/api/fpoDashboardApi";
import { getFpoFarmMonitoring } from "@/features/fpo/api/fpoFarmerApi";

const EMPTY_FARMS = [];

function Metric({ label, value, icon: Icon }) {
  const MetricIcon = Icon;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-black uppercase tracking-wider text-slate-400">{label}</p>
        <MetricIcon className="h-4 w-4 text-emerald-700" />
      </div>
      <p className="mt-2 text-3xl font-black text-slate-950">{value ?? "—"}</p>
    </div>
  );
}

export default function FpoDashboardPage() {
  const report = useQuery({
    queryKey: ["fpo-portfolio-report"],
    queryFn: getFpoDashboardReport,
    staleTime: 30000,
  });
  const farmsQuery = useQuery({
    queryKey: ["fpo-overview-farms"],
    queryFn: () => getFpoFarmMonitoring(),
    staleTime: 30000,
  });
  const farms = farmsQuery.data?.items || EMPTY_FARMS;
  const priorityFarms = useMemo(
    () => farms
      .filter((farm) => ["CRITICAL", "NEEDS_ATTENTION"].includes(farm.overall_status))
      .slice(0, 5),
    [farms],
  );
  const area = farms.reduce((sum, farm) => sum + Number(farm.area_acres || 0), 0);
  const freshness = report.data?.data_freshness?.data_through
    || farms.map((farm) => farm.latest_observation_date || farm.latest_analysis_date).filter(Boolean).sort().at(-1);
  const activeFarmCount = farmsQuery.isSuccess
    ? farms.length
    : report.data?.portfolio?.active_farm_count;

  return (
    <FpoFeatureGate
      feature="BASIC_REPORTS"
      fallback={<div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">Portfolio overview is not enabled for this organization.</div>}
    >
      <div className="space-y-6 pb-10">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-emerald-700">FPO portfolio</p>
            <h1 className="mt-2 text-3xl font-black text-slate-950">Overview</h1>
            <p className="mt-1 text-sm text-slate-500">A concise snapshot of your farmer and farm portfolio.</p>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
            Data through {freshness ? new Date(freshness).toLocaleDateString("en-IN") : "not available"}
          </span>
        </header>

        <section aria-label="Portfolio summary" className="grid gap-4 sm:grid-cols-3">
          <Metric label="Active farmers" value={report.data?.portfolio?.active_farmer_count} icon={CheckCircle2} />
          <Metric label="Active farms" value={activeFarmCount} icon={MapPinned} />
          <Metric label="Area covered" value={farmsQuery.isSuccess ? `${area.toFixed(1)} ac` : "—"} icon={MapPinned} />
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-black text-slate-950">Farms needing attention</h2>
              <p className="mt-1 text-sm text-slate-500">Start with the highest-priority farm follow-ups.</p>
            </div>
            <Link to="/fpo/monitoring" className="text-sm font-bold text-emerald-700">
              Open monitoring <ArrowRight className="inline h-4 w-4" />
            </Link>
          </div>

          {farmsQuery.isLoading ? <p className="mt-4 text-sm text-slate-500">Loading priority farms…</p> : null}
          {farmsQuery.isError ? (
            <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-4 text-sm text-rose-700">
              Unable to load priority farms. Open monitoring to retry.
            </p>
          ) : null}
          {farmsQuery.isSuccess && priorityFarms.length ? (
            <div className="mt-4 space-y-2">
              {priorityFarms.map((farm) => (
                <Link
                  key={farm.farm_id}
                  to={`/fpo/farmers/${farm.farmer_id}/farms/${farm.farm_id}/intelligence`}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 p-3 hover:bg-orange-50"
                >
                  <div>
                    <p className="font-bold text-slate-900">{farm.farm_name || "Unnamed farm"}</p>
                    <p className="text-xs text-slate-500">
                      {farm.district_name || "Location unavailable"} · {farm.crop_name || "Crop unavailable"}
                    </p>
                  </div>
                  <span className="text-xs font-black uppercase text-orange-700">
                    {String(farm.overall_status).replaceAll("_", " ")}
                  </span>
                </Link>
              ))}
            </div>
          ) : null}
          {farmsQuery.isSuccess && !priorityFarms.length ? (
            <p className="mt-4 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">
              No farms currently require priority follow-up.
            </p>
          ) : null}
        </section>
      </div>
    </FpoFeatureGate>
  );
}
