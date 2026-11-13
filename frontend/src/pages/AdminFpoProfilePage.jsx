import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, ClipboardList, ShieldCheck } from "lucide-react";
import { profileApi } from "@/features/profile/api/profileApi";

export default function AdminFpoProfilePage() {
  const { fpoId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { profileApi.getAdminFpoProfile(fpoId).then(setData).catch((item) => setError(item?.message || "Unable to load profile history.")); }, [fpoId]);
  if (error) return <main className="mx-auto max-w-5xl p-6"><p className="rounded-xl bg-rose-50 p-4 text-rose-700">{error}</p></main>;
  if (!data) return <main className="mx-auto max-w-5xl p-6 text-sm text-slate-500">Loading organization profile…</main>;
  const profile = data.profile || {};
  return <main className="mx-auto max-w-6xl space-y-6 p-4 md:p-6">
    <Link to="/admin/fpo-registry" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700"><ArrowLeft className="h-4 w-4" /> FPO registry</Link>
    <header className="rounded-2xl bg-slate-950 p-6 text-white"><p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">Admin · Read-only profile review</p><h1 className="mt-2 text-3xl font-black">{profile.display_name || profile.fpo_name}</h1><p className="mt-2 font-mono text-sm text-slate-300">{data.organization.public_fpo_id}</p><div className="mt-4 flex flex-wrap gap-2 text-xs font-bold"><span className="rounded-full bg-white/10 px-3 py-1.5">Version {profile.profile_version}</span><span className="rounded-full bg-white/10 px-3 py-1.5">Readiness {data.readiness.percentage}%</span>{profile.verification_refresh_required ? <span className="rounded-full bg-amber-400/20 px-3 py-1.5 text-amber-200">Reverification required</span> : null}</div></header>
    {data.reverification_fields?.length ? <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5"><div className="flex gap-3"><AlertTriangle className="h-5 w-5 text-amber-700" /><div><h2 className="font-black text-amber-900">Fields requiring reverification</h2><p className="mt-1 text-sm text-amber-800">The live profile changed after submission. The submitted snapshot remains immutable.</p><div className="mt-3 flex flex-wrap gap-2">{data.reverification_fields.map((field) => <span key={field} className="rounded-full bg-white px-3 py-1 text-xs font-bold text-amber-800">{field}</span>)}</div></div></div></section> : null}
    <div className="grid gap-6 lg:grid-cols-2"><section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-emerald-700" /><h2 className="font-black">Readiness blockers</h2></div>{data.readiness.blocking_requirements?.length ? <ul className="mt-4 space-y-2">{data.readiness.blocking_requirements.map((item) => <li key={item.code} className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">{item.code}</li>)}</ul> : <p className="mt-4 text-sm text-emerald-700">No blocking requirements.</p>}</section><section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><ClipboardList className="h-5 w-5 text-emerald-700" /><h2 className="font-black">Change history</h2></div><div className="mt-4 space-y-3">{data.history?.length ? data.history.map((item) => <div key={item.history_id} className="rounded-lg bg-slate-50 p-3"><p className="text-sm font-bold">v{item.previous_profile_version} → v{item.new_profile_version} · {item.change_classification}</p><p className="mt-1 text-xs text-slate-500">{item.changed_fields.join(", ")}</p></div>) : <p className="text-sm text-slate-500">No profile changes recorded.</p>}</div></section></div>
  </main>;
}
