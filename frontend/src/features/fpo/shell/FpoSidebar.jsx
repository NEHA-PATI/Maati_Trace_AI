import { NavLink } from "react-router-dom";
import { Bell, FileText, LayoutDashboard, Map, Users, UserRound } from "lucide-react";

const items = [
  ["/fpo/dashboard", "Overview", LayoutDashboard],
  ["/fpo/farmers", "Farmers", Users],
  ["/fpo/farms", "Farms", Map],
  ["/fpo/alerts", "Alerts", Bell],
  ["/fpo/reports", "Reports", FileText],
  ["/fpo/profile", "Profile", UserRound],
];

export default function FpoSidebar() {
  return <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block"><div className="border-b border-slate-100 px-6 py-5"><p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-700">MaatiTrace</p><p className="mt-1 text-lg font-black text-slate-950">FPO Portal</p></div><nav className="space-y-1 p-4">{items.map(([to, label, _Icon]) => { const ItemIcon = _Icon; return <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50"}`}><ItemIcon className="h-4 w-4" />{label}</NavLink>; })}</nav></aside>;
}
