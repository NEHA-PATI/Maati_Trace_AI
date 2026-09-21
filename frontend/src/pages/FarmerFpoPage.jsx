import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  discoverFpos,
  getFarmerFpoRelationships,
  requestFarmerFpoRelationship,
  revokeFarmerFpoRelationship,
} from "@/lib/api/fpo";

export default function FarmerFpoPage() {
  const [query, setQuery] = useState("");
  const [fpos, setFpos] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [directory, current] = await Promise.all([discoverFpos(query), getFarmerFpoRelationships()]);
      setFpos(directory || []);
      setRelationships(current || []);
      setError("");
    } catch (requestError) {
      setError(requestError?.message || "Unable to load FPO relationships.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function request(fpoId) {
    setWorking(fpoId);
    try { await requestFarmerFpoRelationship(fpoId); await load(); } catch (requestError) { setError(requestError?.message || "The request could not be sent."); } finally { setWorking(""); }
  }

  async function revoke(relationshipId) {
    setWorking(relationshipId);
    try { await revokeFarmerFpoRelationship(relationshipId); await load(); } catch (requestError) { setError(requestError?.message || "The relationship could not be revoked."); } finally { setWorking(""); }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-6">
      <div><Link to="/farmer/me" className="text-xs font-bold text-emerald-700 hover:underline">← Back to farmer dashboard</Link><h1 className="mt-3 text-2xl font-black text-slate-950">My FPO relationship</h1><p className="mt-1 text-sm text-slate-500">Choose one approved FPO to request membership. Your consent and relationship history are recorded.</p></div>
      {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div> : null}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-900">Relationship history</h2><div className="mt-3 space-y-2">{relationships.length ? relationships.map((item) => <div key={item.relationship_id} className="flex flex-col justify-between gap-3 rounded-xl border border-slate-100 p-4 sm:flex-row sm:items-center"><div><p className="font-semibold text-slate-900">{item.fpo_name || "FPO"}</p><p className="text-xs text-slate-500">{item.public_fpo_id || "ID pending"} · {item.district_name || "District pending"}</p></div><div className="flex items-center gap-2"><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase text-slate-600">{String(item.status).replaceAll("_", " ")}</span>{item.status === "ACTIVE" ? <Button variant="outline" size="sm" onClick={() => revoke(item.relationship_id)} disabled={working === item.relationship_id}>Revoke</Button> : null}</div></div>) : <p className="text-sm text-slate-500">No FPO relationship yet.</p>}</div></section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><h2 className="font-bold text-slate-900">Discover an approved FPO</h2><p className="text-sm text-slate-500">Only approved and discoverable FPOs appear here.</p></div><form onSubmit={(event) => { event.preventDefault(); load(); }} className="flex gap-2"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search name or district" className="rounded-xl border border-slate-300 px-3 py-2 text-sm" /><Button type="submit" size="sm">Search</Button></form></div><div className="mt-4 grid gap-3 md:grid-cols-2">{loading ? <p className="text-sm text-slate-500">Loading approved FPOs…</p> : fpos.length ? fpos.map((fpo) => <div key={fpo.fpo_id} className="rounded-xl border border-slate-100 p-4"><p className="font-semibold text-slate-900">{fpo.fpo_name}</p><p className="mt-1 text-xs text-slate-500">{fpo.public_fpo_id} · {fpo.district_name}, {fpo.state_name}</p><Button className="mt-3" size="sm" onClick={() => request(fpo.fpo_id)} disabled={Boolean(working)}>Request membership</Button></div>) : <p className="text-sm text-slate-500">No approved FPOs match your search.</p>}</div></section>
    </div>
  );
}
