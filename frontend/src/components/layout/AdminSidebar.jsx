import { NavLink } from "react-router-dom";
import { LayoutDashboard, Building2, Users, Sprout, Settings, UserPlus, Activity, Satellite, Database, BarChart3, Layers } from "lucide-react";

const ADMIN_NAVIGATION = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard, iconClass: "text-indigo-500", end: true },
  { to: "/admin/fpo", label: "FPO Management", icon: Building2, iconClass: "text-emerald-500" },
  { to: "/admin/fpo-registry", label: "FPO Registry", icon: Users, iconClass: "text-teal-500" },
  { to: "/admin/crop-observation", label: "Crop Observations", icon: Sprout, iconClass: "text-amber-500" },
  { to: "/admin/system", label: "Feature Processing", icon: Settings, iconClass: "text-violet-500" },
  { to: "/admin/fpo-access", label: "Access Requests", icon: UserPlus, iconClass: "text-sky-500" },
  { to: "/admin/service-health", label: "Service Health", icon: Activity, iconClass: "text-rose-500" },
  { to: "/admin/system?domain=feature-engine", label: "Feature Engine", icon: Sprout, iconClass: "text-violet-500" },
  { to: "/admin/system?domain=raster", label: "Raster Management", icon: Satellite, iconClass: "text-cyan-500" },
  { to: "/admin/system?domain=farm-registry", label: "Farm Registry", icon: Database, iconClass: "text-orange-500" },
  { to: "/admin/system?domain=analytics", label: "Analytics", icon: BarChart3, iconClass: "text-blue-500" },
  { to: "/admin/system?domain=hot-stream", label: "Hot Stream", icon: Layers, iconClass: "text-fuchsia-500" },
];

export default function AdminSidebar() {
  return (
    <aside className="fixed bottom-4 left-0 top-16 z-40 hidden w-64 overflow-hidden rounded-r-2xl border-r border-slate-200 bg-white shadow-sm lg:block">
      <div className="border-b border-slate-100 bg-gradient-to-br from-emerald-50 to-white px-5 py-5">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-700">Admin workspace</p>
        <p className="mt-1 text-sm font-bold text-slate-900">Operations control</p>
      </div>
      <nav aria-label="Admin sections" className="h-[calc(100%-92px)] space-y-1 overflow-y-auto p-3 [scrollbar-width:thin]">
        {ADMIN_NAVIGATION.map(({ to, label, icon, iconClass, end }) => (
          <NavLink key={`${to}-${label}`} to={to} end={end} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-bold transition-colors ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}>
            {createElement(icon, { className: `h-4 w-4 ${iconClass}` })}
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
import { createElement } from "react";
