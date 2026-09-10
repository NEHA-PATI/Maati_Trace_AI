import { useEffect, useState } from "react";
import { AlertTriangle, Camera, Mic2 } from "lucide-react";
import { listIssues } from "../api/cropObservationAdminApi";

export default function CropObservationIssuesPage() {
  const [rows, setRows] = useState(null);
  useEffect(() => { listIssues({ limit: 100, offset: 0 }).then(setRows); }, []);
  if (!rows) return <div className="h-72 animate-pulse rounded-2xl bg-slate-100" />;
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <div className="flex items-center gap-2 font-bold"><AlertTriangle className="h-4 w-4" />Needs attention</div>
        <p className="mt-1">Serious crop status, high severity, “Not sure” issues, and open follow-up records are surfaced here.</p>
      </div>
      <div className="grid gap-3 xl:grid-cols-2">
        {rows.map((row) => (
          <div key={row.record_id} className="rounded-2xl border bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div><div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{row.observed_on}</div><div className="mt-1 font-black text-slate-900">{row.crop_code} · {row.practice_code.replaceAll('_',' ')}</div><div className="mt-1 text-sm text-slate-600">{row.stage_code.replaceAll('_',' ')}</div></div>
              <span className="rounded-full bg-rose-50 px-2.5 py-1 text-xs font-bold text-rose-700">{row.severity || row.crop_status.replaceAll('_',' ')}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-600"><span>Issue: <b>{row.issue_code || '—'}</b></span><span className="inline-flex items-center gap-1"><Camera className="h-4 w-4" />{row.issue_image_count}</span><span className="inline-flex items-center gap-1"><Mic2 className="h-4 w-4" />{row.voice_count}</span><span>Review: <b>{row.review_status.replaceAll('_',' ')}</b></span></div>
          </div>
        ))}
        {!rows.length ? <p className="text-sm text-slate-500">No attention items right now.</p> : null}
      </div>
    </div>
  );
}
