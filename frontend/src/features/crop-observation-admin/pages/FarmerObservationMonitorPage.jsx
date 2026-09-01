import { useEffect, useState } from "react";

import {
  getObservationDetail,
  getObservationsSummary,
  listObservations,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";

const STATUS_TONE = {
  GOOD: "bg-emerald-100 text-emerald-700",
  SOME_PROBLEM: "bg-amber-100 text-amber-700",
  SERIOUS_PROBLEM: "bg-rose-100 text-rose-700",
};

export default function FarmerObservationMonitorPage() {
  const [summary, setSummary] = useState(null);
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [summaryData, listData] = await Promise.all([
        getObservationsSummary(),
        listObservations({ status: status || undefined, limit: 50 }),
      ]);
      setSummary(summaryData);
      setItems(listData);
    } catch (err) {
      setError(err?.message || "Could not load observations.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  async function openDetail(id) {
    try {
      setDetail(await getObservationDetail(id));
    } catch (err) {
      setError(err?.message || "Could not load detail.");
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-2xl font-black text-slate-950">Farmer Observations</h1>

      {summary ? (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Total" value={summary.total_observations} />
          <StatTile label="Today" value={summary.today_count} />
          <StatTile label="Serious" value={summary.serious_count} tone="text-rose-600" />
          <StatTile label="Open flags" value={summary.open_review_flags} tone="text-amber-600" />
        </div>
      ) : null}

      <div className="mt-6 flex items-center gap-2">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="h-9 rounded-md border border-slate-200 px-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="GOOD">Good</option>
          <option value="SOME_PROBLEM">Some problem</option>
          <option value="SERIOUS_PROBLEM">Serious problem</option>
        </select>
      </div>

      {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
      {loading ? <p className="mt-3 text-sm text-slate-400">Loading…</p> : null}

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Crop</th>
              <th className="px-3 py-2">Stage</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.daily_observation_id}
                onClick={() => openDetail(item.daily_observation_id)}
                className="cursor-pointer border-t border-slate-100 hover:bg-slate-50"
              >
                <td className="px-3 py-2">{item.observed_on}</td>
                <td className="px-3 py-2">{item.crop_code}</td>
                <td className="px-3 py-2">{item.stage_code}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_TONE[item.crop_status]}`}>
                    {item.crop_status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && items.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-slate-400">No observations match this filter.</p>
        ) : null}
      </div>

      {detail ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setDetail(null)}>
          <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold text-slate-950">
              {detail.crop_code} — {detail.stage_code}
            </h2>
            <p className="text-sm text-slate-500">{detail.observed_on}</p>
            <p className="mt-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_TONE[detail.crop_status]}`}>
                {detail.crop_status}
              </span>
            </p>
            <div className="mt-4 space-y-2">
              {detail.practices.map((p) => (
                <div key={p.practice_code} className="rounded-lg bg-slate-50 p-3">
                  <p className="text-sm font-semibold text-slate-800">{p.practice_code}</p>
                  <pre className="mt-1 overflow-x-auto text-xs text-slate-600">{JSON.stringify(p.answers, null, 2)}</pre>
                </div>
              ))}
              {detail.practices.length === 0 ? <p className="text-sm text-slate-400">No practices logged.</p> : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function StatTile({ label, value, tone = "text-slate-950" }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <div className={`text-2xl font-black ${tone}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}
