import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, FileCheck2, RefreshCw, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import {
  assignFpoClass,
  getFpoVerificationQueue,
  reviewFpoVerification,
  runFpoReconciliation,
} from "@/lib/api/fpo";

const TABS = ["verification", "configuration"];
const FILTERS = [
  ["", "All submissions"],
  ["PROFILE_INCOMPLETE", "Onboarding"],
  ["SUBMITTED", "Submitted"],
  ["UNDER_REVIEW", "Under review"],
  ["CHANGES_REQUIRED", "Changes required"],
  ["APPROVED", "Approved"],
  ["REJECTED", "Rejected"],
];

function readableStatus(value) {
  return String(value || "PROFILE_INCOMPLETE").replaceAll("_", " ");
}

export default function FpoAdminPage() {
  const [tab, setTab] = useState("verification");
  const [filter, setFilter] = useState("");
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [note, setNote] = useState("");
  const [classCode, setClassCode] = useState("A");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [reconciliation, setReconciliation] = useState(null);

  async function loadQueue() {
    setLoading(true);
    setError("");
    try {
      setItems(await getFpoVerificationQueue(filter));
    } catch (requestError) {
      setError(requestError?.message || "Unable to load FPO verification submissions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadQueue();
  }, [filter]);

  const counts = useMemo(() => items.reduce((result, item) => {
    const key = item.verification_status || "PROFILE_INCOMPLETE";
    result[key] = (result[key] || 0) + 1;
    return result;
  }, {}), [items]);

  async function decide(status) {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      await reviewFpoVerification(selected.fpo_id, status, note);
      setSelected(null);
      setNote("");
      await loadQueue();
    } catch (requestError) {
      setError(requestError?.message || "The verification decision could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function assignClass() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      await assignFpoClass(selected.fpo_id, classCode);
      await loadQueue();
    } catch (requestError) {
      setError(requestError?.message || "The FPO class could not be assigned.");
    } finally {
      setSaving(false);
    }
  }

  async function reconcile() {
    setSaving(true);
    setError("");
    try {
      setReconciliation(await runFpoReconciliation());
    } catch (requestError) {
      setError(requestError?.message || "The FPO reconciliation could not be completed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-emerald-600">Admin / FPO</p>
          <h1 className="mt-1 text-2xl font-black text-slate-950">FPO management</h1>
          <p className="mt-1 text-sm text-slate-500">Review onboarding, verification, and organization controls from one workspace.</p>
        </div>
        <Button variant="outline" onClick={loadQueue} disabled={loading} className="rounded-xl">
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </Button>
      </div>

      <div className="flex gap-2 border-b border-slate-200">
        {TABS.map((value) => (
          <button key={value} type="button" onClick={() => setTab(value)} className={`border-b-2 px-4 py-3 text-sm font-bold capitalize ${tab === value ? "border-emerald-600 text-emerald-700" : "border-transparent text-slate-500"}`}>
            {value}
          </button>
        ))}
      </div>

      {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div> : null}

      {tab === "configuration" ? (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-5">
            <div><p className="font-bold text-emerald-950">Data integrity reconciliation</p><p className="mt-1 text-sm text-emerald-800">Repair safe farmer-to-FPO projection drift and report provisioning gaps.</p></div>
            <Button onClick={reconcile} disabled={saving} className="rounded-xl bg-emerald-700 hover:bg-emerald-800"><RefreshCw className={`mr-2 h-4 w-4 ${saving ? "animate-spin" : ""}`} /> Run reconciliation</Button>
          </div>
          {reconciliation ? <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Completed: repaired {reconciliation.repaired_farmer_projections}, cleared {reconciliation.cleared_stale_projections}, orphaned organizations {reconciliation.orphaned_organizations}.</div> : null}
          <div className="grid gap-4 md:grid-cols-3">
          {[
            ["Verification policy", "Profile completion is required before submission. Approval enables discovery."],
            ["Organization model", "One active owner account per FPO. Staff accounts are disabled for this release."],
            ["Provisioning", "New FPO accounts are provisioned through the auth outbox worker with retry support."],
          ].map(([title, description]) => <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="font-bold text-slate-900">{title}</p><p className="mt-2 text-sm leading-6 text-slate-500">{description}</p><span className="mt-4 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">Active</span></div>)}
          </div>
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            {[["SUBMITTED", "Awaiting review"], ["UNDER_REVIEW", "In review"], ["APPROVED", "Approved"]].map(([key, label]) => <div key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-2 text-2xl font-black text-slate-950">{counts[key] || 0}</p></div>)}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap gap-2 border-b border-slate-100 p-4">
              {FILTERS.map(([value, label]) => <button key={value} type="button" onClick={() => setFilter(value)} className={`rounded-full px-3 py-1.5 text-xs font-bold ${filter === value ? "bg-emerald-700 text-white" : "bg-slate-100 text-slate-600"}`}>{label}</button>)}
            </div>
            {loading ? <p className="p-6 text-sm text-slate-500">Loading FPO submissions…</p> : items.length === 0 ? <p className="p-8 text-center text-sm text-slate-500">No FPO submissions in this queue.</p> : <div className="divide-y divide-slate-100">{items.map((item) => <div key={item.fpo_id} className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between"><div><div className="flex flex-wrap items-center gap-3"><p className="font-bold text-slate-900">{item.fpo_name || "FPO profile pending"}</p><VerificationStamp label={readableStatus(item.verification_status)} type={item.verification_status === "APPROVED" ? "success" : "pending"} compact /></div><p className="mt-1 text-xs text-slate-500">{item.public_fpo_id || "Public ID pending"} · {item.district_name || "District pending"}, {item.state_name || "State pending"}</p><p className="mt-2 text-sm text-slate-600">Representative: {item.contact_person_name || "Pending"} · {item.contact_email || "No email"}</p></div><Button variant="outline" className="rounded-xl" onClick={() => { setSelected(item); setNote(item.reviewer_note || ""); }}><FileCheck2 className="mr-2 h-4 w-4" /> Review</Button></div>)}</div>}
          </div>
        </>
      )}

      {selected ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4" role="dialog" aria-modal="true"><div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl"><p className="text-xs font-bold uppercase tracking-wider text-emerald-600">Verification decision</p><h2 className="mt-1 text-xl font-black text-slate-950">{selected.fpo_name || "FPO profile"}</h2><p className="mt-2 text-sm text-slate-500">{selected.registration_type || "Registration type pending"} · {selected.registration_number || "Registration number pending"}</p><label className="mt-5 block text-sm font-bold text-slate-700" htmlFor="review-note">Reviewer note</label><textarea id="review-note" value={note} onChange={(event) => setNote(event.target.value)} rows={4} placeholder="Add a reason or review note…" className="mt-2 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-emerald-600" /><div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3"><label htmlFor="fpo-class" className="block text-xs font-bold uppercase tracking-wider text-slate-500">FPO class</label><div className="mt-2 flex gap-2"><select id="fpo-class" value={classCode} onChange={(event) => setClassCode(event.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"><option value="A">Class A · Foundation</option><option value="B">Class B · Growth</option><option value="C">Class C · Commercial</option></select><Button variant="outline" onClick={assignClass} disabled={saving}>Assign class</Button></div></div><div className="mt-5 flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => setSelected(null)} disabled={saving}>Cancel</Button><Button variant="outline" onClick={() => decide("CHANGES_REQUIRED")} disabled={saving}><XCircle className="mr-2 h-4 w-4 text-amber-600" /> Request changes</Button><Button variant="outline" onClick={() => decide("REJECTED")} disabled={saving}><XCircle className="mr-2 h-4 w-4 text-rose-600" /> Reject</Button><Button onClick={() => decide("APPROVED")} disabled={saving} className="bg-emerald-700 hover:bg-emerald-800"><CheckCircle2 className="mr-2 h-4 w-4" /> Accept</Button></div></div></div> : null}
    </div>
  );
}
