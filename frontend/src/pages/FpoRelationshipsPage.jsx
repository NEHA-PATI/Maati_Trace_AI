import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { decideFpoRelationship, getFpoRelationships } from "@/lib/api/fpo";

export default function FpoRelationshipsPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [working, setWorking] = useState("");

  async function load() {
    try { setItems(await getFpoRelationships()); setError(""); } catch (requestError) { setError(requestError?.message || "Unable to load farmer requests."); }
  }

  useEffect(() => { load(); }, []);

  async function decide(id, decision) {
    setWorking(id);
    try { await decideFpoRelationship(id, decision); await load(); } catch (requestError) { setError(requestError?.message || "The relationship decision could not be saved."); } finally { setWorking(""); }
  }

  return <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-6"><div><Link to="/fpo/me" className="text-xs font-bold text-emerald-700 hover:underline">← Back to FPO dashboard</Link><h1 className="mt-3 text-2xl font-black text-slate-950">Farmer relationships</h1><p className="mt-1 text-sm text-slate-500">Review farmer consent requests. Accepting creates the active primary FPO relationship.</p></div>{error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div> : null}<div className="rounded-2xl border border-slate-200 bg-white shadow-sm">{items.length ? <div className="divide-y divide-slate-100">{items.map((item) => <div key={item.relationship_id} className="flex flex-col justify-between gap-4 p-5 sm:flex-row sm:items-center"><div><p className="font-semibold text-slate-900">{item.full_name || "Farmer"}</p><p className="text-xs text-slate-500">{item.email || item.phone_number || "Contact unavailable"} · {item.district_name || "District pending"}</p><span className="mt-2 inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase text-slate-600">{String(item.status).replaceAll("_", " ")}</span></div>{item.status === "PENDING_FPO_ACCEPTANCE" ? <div className="flex gap-2"><Button variant="outline" onClick={() => decide(item.relationship_id, "REJECTED")} disabled={Boolean(working)}>Reject</Button><Button onClick={() => decide(item.relationship_id, "ACTIVE")} disabled={Boolean(working)} className="bg-emerald-700 hover:bg-emerald-800">Accept</Button></div> : null}</div>)}</div> : <p className="p-8 text-center text-sm text-slate-500">No farmer relationship requests yet.</p>}</div></div>;
}
