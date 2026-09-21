import { useFpoPortal } from "./FpoPortalContext";

export default function FpoTopbar() {
  const { bootstrap } = useFpoPortal();
  const organization = bootstrap?.organization;
  const verification = bootstrap?.verification?.status;
  return <header className="flex min-h-16 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-8"><div><p className="text-sm font-bold text-slate-950">{organization?.display_name || "FPO workspace"}</p><p className="text-xs text-slate-500">{organization?.public_fpo_id || "Preparing organization"}</p></div><div className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">{verification || "ONBOARDING"}</div></header>;
}
