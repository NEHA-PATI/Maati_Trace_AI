import { NavLink } from "react-router-dom";

export default function FpoMobileNavigation() {
  return <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-slate-200 bg-white p-2 lg:hidden">{[["/fpo/dashboard", "Overview"], ["/fpo/farmers", "Farmers"], ["/fpo/monitoring", "Monitor"], ["/fpo/alerts", "Alerts"], ["/fpo/profile", "Profile"]].map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) => `rounded-lg py-2 text-center text-[11px] font-bold ${isActive ? "text-emerald-700" : "text-slate-500"}`}>{label}</NavLink>)}</nav>;
}
