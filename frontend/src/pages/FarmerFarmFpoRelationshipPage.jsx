import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cancelFarmerFpoRelationship, getFarmerFpoRelationships, revokeFarmerFpoRelationship } from "@/lib/api/fpo";

const formatDate = (value) => value ? new Date(value).toLocaleString() : "Not recorded";
const pretty = (value) => String(value || "Not provided").replaceAll("_", " ");

export default function FarmerFarmFpoRelationshipPage() {
  const { farmId, relationshipId } = useParams();
  const navigate = useNavigate();
  const [relationship, setRelationship] = useState(null);
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);

  useEffect(() => {
    getFarmerFpoRelationships().then((rows) => {
      const found = (Array.isArray(rows) ? rows : rows?.items || []).find((row) => String(row.relationship_id) === relationshipId && String(row.farm_id) === farmId);
      if (!found) throw new Error("This farm connection was not found for your account.");
      setRelationship(found);
    }).catch((e) => setError(e?.message || "Unable to load this farm connection."));
  }, [farmId, relationshipId]);

  async function endConnection() {
    if (!relationship) return;
    setWorking(true);
    try {
      if (relationship.status === "ACTIVE") await revokeFarmerFpoRelationship(farmId, relationshipId);
      else await cancelFarmerFpoRelationship(relationshipId);
      navigate(`/farmer/fpo?farm_id=${encodeURIComponent(farmId)}`, { replace: true });
    } catch (e) {
      setError(e?.message || "Unable to update this connection.");
    } finally {
      setWorking(false);
    }
  }

  return <main className="mx-auto max-w-3xl space-y-5 p-4 pb-24 md:p-8"><Link to={`/farmer/fpo?farm_id=${encodeURIComponent(farmId)}`} className="inline-flex items-center gap-2 text-sm font-bold text-emerald-800"><ArrowLeft className="h-4 w-4" />Back to FPOs</Link>{error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div> : null}{relationship ? <><header className="rounded-3xl bg-emerald-900 p-6 text-white"><p className="text-xs font-black uppercase tracking-[0.18em] text-emerald-200">Farm connection</p><h1 className="mt-2 text-3xl font-black">{relationship.fpo_name || "FPO"}</h1><p className="mt-2 text-sm text-emerald-100">{relationship.public_fpo_id || "FPO ID not available"} · {relationship.farm_name || "Selected farm"}</p><span className="mt-4 inline-flex rounded-full bg-white/15 px-3 py-1 text-xs font-black uppercase">{pretty(relationship.status)}</span></header><section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-emerald-700" /><h2 className="text-lg font-black">What is shared</h2></div><p className="mt-2 text-sm leading-6 text-slate-600">This relationship applies only to this farm. It does not grant access to your other farms. You may revoke active access or cancel a pending request below.</p><dl className="mt-4 grid gap-3 sm:grid-cols-2">{[["Farm", relationship.farm_name], ["Area", relationship.area_acres != null ? `${relationship.area_acres} acres` : null], ["Location", [relationship.village_name, relationship.block_name, relationship.farm_district_name, relationship.farm_state_name].filter(Boolean).join(", ")], ["Crop", relationship.crop_name || relationship.crop_code], ["Policy", relationship.policy_code ? `${relationship.policy_code} v${relationship.policy_version}` : null], ["Consent date", formatDate(relationship.consent_captured_at || relationship.farmer_consented_at)], ["Consent language", relationship.language_code], ["Permitted scopes", (relationship.scopes || []).map(pretty).join(", ")], ["Request date", formatDate(relationship.created_at)]].map(([title, value]) => <div key={title} className="rounded-xl bg-slate-50 p-3"><dt className="text-[10px] font-black uppercase tracking-wide text-slate-400">{title}</dt><dd className="mt-1 text-sm font-semibold text-slate-800">{value || "Not provided"}</dd></div>)}</dl></section><div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => navigate(`/land/${farmId}`)}>Open this farm</Button>{["ACTIVE", "PENDING_FPO_ACCEPTANCE"].includes(relationship.status) ? <Button variant="outline" className="text-rose-700" onClick={endConnection} disabled={working}>{working ? "Updating…" : relationship.status === "ACTIVE" ? "Revoke farm access" : "Cancel request"}</Button> : null}</div></> : !error ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading connection details…</div> : null}</main>;
}
