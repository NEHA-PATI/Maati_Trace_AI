import { createElement, useEffect, useState } from "react";
import { AlertTriangle, Camera, ClipboardList, Mic2, Sprout, Users, Warehouse } from "lucide-react";

import { getOverview } from "../api/cropObservationAdminApi";

function Metric({ label, value, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-black text-slate-900">{Number(value || 0).toLocaleString()}</p>
        </div>
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-50 text-emerald-700">
          {createElement(Icon, { className: "h-5 w-5" })}
        </span>
      </div>
    </div>
  );
}

function Bars({ title, items, labelKey }) {
  const max = Math.max(1, ...items.map((item) => Number(item.records || 0)));
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="font-bold text-slate-900">{title}</h3>
      <div className="mt-4 space-y-3">
        {items.length ? items.map((item) => (
          <div key={item[labelKey]}>
            <div className="mb-1 flex items-center justify-between gap-3 text-sm">
              <span className="font-medium text-slate-700">{String(item[labelKey]).replaceAll("_", " ")}</span>
              <span className="font-bold text-slate-900">{item.records}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-emerald-600" style={{ width: `${Math.max(4, (item.records / max) * 100)}%` }} />
            </div>
          </div>
        )) : <p className="text-sm text-slate-500">No records yet.</p>}
      </div>
    </section>
  );
}

export default function CropObservationOverviewPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getOverview().then((value) => !cancelled && setData(value)).catch((err) => !cancelled && setError(err?.message || "Could not load overview."));
    return () => { cancelled = true; };
  }, []);

  if (error) return <div className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
  if (!data) return <div className="h-72 animate-pulse rounded-2xl bg-slate-100" />;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Practice records" value={data.records} icon={ClipboardList} />
        <Metric label="Farmers reporting" value={data.farmers} icon={Users} />
        <Metric label="Farms reporting" value={data.farms} icon={Warehouse} />
        <Metric label="Open reviews" value={data.open_reviews} icon={AlertTriangle} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Serious crop updates" value={data.serious_stage_updates} icon={AlertTriangle} />
        <Metric label="Problem images" value={data.issue_images} icon={Camera} />
        <Metric label="Action images" value={data.practice_images} icon={Sprout} />
        <Metric label="Voice notes" value={data.voice_notes} icon={Mic2} />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Bars title="Records by crop" items={data.by_crop || []} labelKey="crop_code" />
        <Bars title="Records by practice" items={data.by_practice || []} labelKey="practice_code" />
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center gap-5 text-sm">
          <span><b>{data.good_stage_updates}</b> good updates</span>
          <span><b>{data.some_problem_stage_updates}</b> some-problem updates</span>
          <span><b>{data.high_severity_records}</b> high-severity practice records</span>
          <span><b>{data.open_flags}</b> open automatic flags</span>
        </div>
      </section>
    </div>
  );
}
