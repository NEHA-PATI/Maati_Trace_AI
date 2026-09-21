import { useEffect, useMemo, useRef, useState } from "react";
import { Camera, ChevronRight, Mic2, X } from "lucide-react";

import {
  fetchAdminMediaBlob,
  getPracticeRecord,
  listPracticeRecords,
  updatePracticeRecordReview,
} from "../api/cropObservationAdminApi";

const REVIEW_OPTIONS = ["NEW", "IN_REVIEW", "NEEDS_FOLLOW_UP", "REVIEWED", "RESOLVED"];

function fmt(value) {
  if (!value) return "—";
  try { return new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); }
  catch { return value; }
}

function pill(value) {
  const v = String(value || "");
  if (v === "SERIOUS_PROBLEM" || v === "HIGH") return "bg-rose-50 text-rose-700 border-rose-200";
  if (v === "SOME_PROBLEM" || v === "MEDIUM" || v === "NEEDS_FOLLOW_UP") return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-emerald-50 text-emerald-700 border-emerald-200";
}

export function RecordDrawer({ recordId, onClose, onUpdated }) {
  const [record, setRecord] = useState(null);
  const [note, setNote] = useState("");
  const [review, setReview] = useState("NEW");
  const [mediaUrls, setMediaUrls] = useState({});
  const createdUrls = useRef([]);

  useEffect(() => {
    let cancelled = false;
    getPracticeRecord(recordId).then(async (value) => {
      if (cancelled) return;
      setRecord(value);
      setNote(value.admin_note || "");
      setReview(value.review_status || "NEW");
      const pairs = await Promise.all((value.media || []).map(async (item) => {
        try {
          const blob = await fetchAdminMediaBlob(item.content_url);
          const url = URL.createObjectURL(blob);
          createdUrls.current.push(url);
          return [item.media_asset_id, url];
        } catch { return [item.media_asset_id, null]; }
      }));
      if (!cancelled) setMediaUrls(Object.fromEntries(pairs));
    });
    return () => {
      cancelled = true;
      createdUrls.current.forEach((url) => URL.revokeObjectURL(url));
      createdUrls.current = [];
    };
  }, [recordId]);

  async function saveReview() {
    await updatePracticeRecordReview(recordId, { review_status: review, admin_note: note || null });
    setRecord((prev) => ({ ...prev, review_status: review, admin_note: note }));
    onUpdated?.();
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/30" onClick={onClose}>
      <aside className="ml-auto h-full w-full max-w-[620px] overflow-y-auto bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Practice record</p>
            <h2 className="font-black text-slate-900">{recordId.slice(0, 8).toUpperCase()}</h2>
          </div>
          <button onClick={onClose} className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100"><X className="h-4 w-4" /></button>
        </div>
        {!record ? <div className="m-5 h-64 animate-pulse rounded-xl bg-slate-100" /> : (
          <div className="space-y-6 p-5">
            <div className="grid gap-3 sm:grid-cols-2">
              {[['Date', fmt(record.observed_on)], ['Crop', record.crop_code], ['Stage', record.stage_code], ['Practice', record.practice_code], ['Farmer', record.farmer_user_id], ['Farm', record.farm_id]].map(([label, value]) => (
                <div key={label} className="rounded-xl border bg-slate-50 p-3"><div className="text-xs font-semibold text-slate-500">{label}</div><div className="mt-1 break-all text-sm font-bold text-slate-900">{String(value).replaceAll('_',' ')}</div></div>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              <span className={`rounded-full border px-3 py-1 text-xs font-bold ${pill(record.crop_status)}`}>{record.crop_status.replaceAll('_',' ')}</span>
              {record.severity ? <span className={`rounded-full border px-3 py-1 text-xs font-bold ${pill(record.severity)}`}>Severity {record.severity}</span> : null}
            </div>

            <section>
              <h3 className="font-bold text-slate-900">Farmer input</h3>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {Object.entries(record.answers || {}).map(([key, value]) => (
                  <div key={key} className="rounded-xl border p-3"><div className="text-xs font-semibold text-slate-500">{key.replaceAll('_',' ')}</div><div className="mt-1 text-sm font-semibold text-slate-900">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</div></div>
                ))}
              </div>
            </section>

            {['ISSUE_EVIDENCE','PRACTICE_EVIDENCE'].map((purpose) => {
              const items = (record.media || []).filter((m) => m.media_purpose === purpose && m.media_type === 'IMAGE');
              if (!items.length) return null;
              return <section key={purpose}><h3 className="font-bold text-slate-900">{purpose === 'ISSUE_EVIDENCE' ? 'Problem evidence' : 'Practice / action evidence'}</h3><div className="mt-3 flex flex-wrap gap-3">{items.map((m) => mediaUrls[m.media_asset_id] ? <img key={m.media_asset_id} src={mediaUrls[m.media_asset_id]} alt="" className="h-32 w-32 rounded-xl object-cover" /> : <div key={m.media_asset_id} className="h-32 w-32 rounded-xl bg-slate-100" />)}</div></section>;
            })}

            {(record.media || []).some((m) => m.media_type === 'AUDIO') ? (
              <section><h3 className="font-bold text-slate-900">Farmer voice</h3><div className="mt-3 space-y-2">{record.media.filter((m) => m.media_type === 'AUDIO').map((m) => mediaUrls[m.media_asset_id] ? <audio key={m.media_asset_id} src={mediaUrls[m.media_asset_id]} controls className="w-full" /> : null)}</div></section>
            ) : null}

            <section className="rounded-2xl border bg-slate-50 p-4">
              <h3 className="font-bold text-slate-900">Review</h3>
              <select value={review} onChange={(e) => setReview(e.target.value)} className="mt-3 h-11 w-full rounded-xl border bg-white px-3 text-sm font-semibold">{REVIEW_OPTIONS.map((v) => <option key={v} value={v}>{v.replaceAll('_',' ')}</option>)}</select>
              <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={4} placeholder="Internal admin / agronomist note" className="mt-3 w-full rounded-xl border bg-white p-3 text-sm" />
              <button onClick={saveReview} className="mt-3 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-bold text-white">Save review</button>
            </section>
          </div>
        )}
      </aside>
    </div>
  );
}

export default function CropObservationRecordsPage() {
  const [filters, setFilters] = useState({ crop_code: "", practice_code: "", crop_status: "", review_status: "" });
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const query = useMemo(() => ({ ...filters, limit: 100, offset: 0 }), [filters]);

  function load() {
    setLoading(true);
    listPracticeRecords(query).then(setRows).finally(() => setLoading(false));
  }
  useEffect(load, [query]);

  return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-2xl border bg-white p-4 md:grid-cols-4">
        {[['crop_code','Crop code'],['practice_code','Practice'],['crop_status','Crop status'],['review_status','Review status']].map(([key, placeholder]) => (
          <input key={key} value={filters[key]} onChange={(e) => setFilters((p) => ({ ...p, [key]: e.target.value }))} placeholder={placeholder} className="h-10 rounded-xl border px-3 text-sm" />
        ))}
      </div>
      <div className="overflow-hidden rounded-2xl border bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-[1050px] w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr>{['Date','Crop','Stage','Practice','Status','Severity','Evidence','Review',''].map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr></thead>
            <tbody className="divide-y">
              {loading ? <tr><td colSpan="9" className="p-8 text-center text-slate-500">Loading…</td></tr> : rows.map((row) => (
                <tr key={row.record_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-semibold">{fmt(row.observed_on)}</td>
                  <td className="px-4 py-3">{row.crop_code}</td>
                  <td className="px-4 py-3">{row.stage_code.replaceAll('_',' ')}</td>
                  <td className="px-4 py-3 font-semibold">{row.practice_code.replaceAll('_',' ')}</td>
                  <td className="px-4 py-3"><span className={`rounded-full border px-2 py-1 text-xs font-bold ${pill(row.crop_status)}`}>{row.crop_status.replaceAll('_',' ')}</span></td>
                  <td className="px-4 py-3">{row.severity || '—'}</td>
                  <td className="px-4 py-3"><div className="flex gap-3 text-slate-600"><span className="inline-flex items-center gap-1"><Camera className="h-4 w-4" />{row.issue_image_count + row.practice_image_count}</span><span className="inline-flex items-center gap-1"><Mic2 className="h-4 w-4" />{row.voice_count}</span></div></td>
                  <td className="px-4 py-3">{row.review_status.replaceAll('_',' ')}</td>
                  <td className="px-4 py-3"><button onClick={() => setSelected(row.record_id)} className="grid h-8 w-8 place-items-center rounded-lg hover:bg-slate-100"><ChevronRight className="h-4 w-4" /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {selected ? <RecordDrawer recordId={selected} onClose={() => setSelected(null)} onUpdated={load} /> : null}
    </div>
  );
}
