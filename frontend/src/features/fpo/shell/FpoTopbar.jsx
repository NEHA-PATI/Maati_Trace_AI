import { NavLink } from "react-router-dom";
import { useFpoPortal } from "./FpoPortalContext";
import LogoutButton from "@/features/auth/components/LogoutButton";
import { LanguageToggle } from "@/features/language";

export default function FpoTopbar() {
  const { bootstrap } = useFpoPortal();
  const organization = bootstrap?.organization;
  const verification = bootstrap?.verification?.status;
  return <header className="border-b border-slate-200 bg-white px-4 md:px-8"><div className="flex min-h-16 items-center justify-between gap-4"><div className="min-w-0"><p className="truncate text-sm font-bold text-slate-950">{organization?.display_name || "FPO workspace"}</p><p className="truncate text-xs text-slate-500">{organization?.public_fpo_id || "Preparing organization"}</p></div><div className="flex items-center gap-3"><LanguageToggle /><span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 sm:inline-flex">{verification || "ONBOARDING"}</span><LogoutButton className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" /></div></div><nav aria-label="FPO primary navigation" className="flex gap-1 overflow-x-auto pb-2 lg:hidden">{[["/fpo/overview", "Overview"], ["/fpo/farmers", "Farmers"], ["/fpo/relationships", "Farm requests"], ["/fpo/farms", "Farms"], ["/fpo/monitoring", "Monitoring"], ["/fpo/alerts", "Alerts"], ["/fpo/profile", "Profile"]].map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) => `whitespace-nowrap rounded-lg px-3 py-2 text-xs font-bold ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-500"}`}>{label}</NavLink>)}</nav></header>;
}
