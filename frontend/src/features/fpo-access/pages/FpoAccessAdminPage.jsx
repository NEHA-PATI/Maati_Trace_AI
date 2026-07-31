import { useCallback, useEffect, useState } from "react";
import { fpoAccessApi } from "@/features/fpo-access/api/fpoAccessApi";

export default function FpoAccessAdminPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [pending, approved] = await Promise.all([
        fpoAccessApi.listForAdmin({ status: "pending" }),
        fpoAccessApi.listForAdmin({ status: "approved" }),
      ]);
      setItems([...(pending.items || []), ...(approved.items || [])]);
    } catch (requestError) {
      setError(requestError.message || "FPO access requests could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function reject(item) {
    setBusyId(item.request_id);
    setError("");
    setNotice("");
    try {
      await fpoAccessApi.reviewForAdmin(item.request_id, {
        status: "rejected",
        review_note: "Request rejected by administrator.",
      });
      setNotice(`Rejected ${item.organisation_name}.`);
      await load();
    } catch (requestError) {
      setError(requestError.message || "The request could not be rejected.");
    } finally {
      setBusyId("");
    }
  }

  async function approveAndInvite(item) {
    setBusyId(item.request_id);
    setError("");
    setNotice("");
    try {
      if (item.status === "pending") {
        await fpoAccessApi.reviewForAdmin(item.request_id, {
          status: "approved",
          review_note: "Approved for secure FPO invitation.",
        });
      }
      await fpoAccessApi.createInvitation({
        email: item.contact_email,
        role: "fpo",
        metadata: {
          organisation_name: item.organisation_name,
          contact_person_name: item.contact_person_name,
          access_request_id: item.request_id,
        },
      });
      await fpoAccessApi.reviewForAdmin(item.request_id, {
        status: "closed",
        review_note: "FPO invitation queued successfully.",
      });
      setNotice(`Invitation queued for ${item.contact_email}.`);
      await load();
    } catch (requestError) {
      setError(`${requestError.message || "The invitation could not be queued."} Approved requests remain available for invitation retry.`);
      await load();
    } finally {
      setBusyId("");
    }
  }

  return (
    <section className="space-y-5 p-6">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">Authentication administration</p>
        <h1 className="mt-1 text-3xl font-black text-slate-950">FPO access and invitations</h1>
        <p className="mt-2 text-sm text-slate-600">Pending requests can be reviewed. Approved requests stay here until an invitation is successfully queued.</p>
      </div>
      {notice ? <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">{notice}</div> : null}
      {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
      {loading ? <p className="text-sm text-slate-500">Loading requests…</p> : null}
      {!loading && items.length === 0 ? <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">No pending or approved FPO requests.</p> : null}
      <div className="grid gap-4">
        {items.map((item) => {
          const busy = busyId === item.request_id;
          return (
            <article key={item.request_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-bold text-slate-950">{item.organisation_name}</h2>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold uppercase text-slate-600">{item.status}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{item.contact_person_name} · {item.contact_email} · {item.contact_phone}</p>
                  <p className="mt-1 text-sm text-slate-500">{[item.district_name, item.state_name].filter(Boolean).join(", ")}</p>
                  {item.registration_number ? <p className="mt-1 text-xs text-slate-500">Registration: {item.registration_number}</p> : null}
                  {item.message ? <p className="mt-3 text-sm leading-6 text-slate-700">{item.message}</p> : null}
                </div>
                <div className="flex gap-2">
                  {item.status === "pending" ? (
                    <button type="button" disabled={busy} onClick={() => reject(item)} className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 disabled:opacity-50">Reject</button>
                  ) : null}
                  <button type="button" disabled={busy} onClick={() => approveAndInvite(item)} className="rounded-lg bg-emerald-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">
                    {busy ? "Working…" : item.status === "approved" ? "Retry invitation" : "Approve and invite"}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
