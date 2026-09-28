import { NavLink } from "react-router-dom";
import { useFpoPortal } from "./FpoPortalContext";
import { Bell, FileText, LayoutDashboard, Map, Users, UserRound, UploadCloud, ShieldCheck, Layers, CalendarDays, ListTodo, SlidersHorizontal, MessageCircle, Sprout, BarChart3, FileOutput, BriefcaseBusiness, PackageCheck, Route, FileCheck, PlugZap, Link2 } from "lucide-react";

const items = [
  ["/fpo/overview", "Overview", LayoutDashboard],
  ["/fpo/farmers", "Farmers", Users],
  ["/fpo/farms", "Farms", Map],
  ["/fpo/relationships", "Farm requests", Link2],
  ["/fpo/monitoring", "Monitoring", Map],
  ["/fpo/alerts", "Alerts", Bell],
  ["/fpo/reports", "Reports", FileText],
  ["/fpo/imports", "Bulk onboarding", UploadCloud],
  ["/fpo/data-quality", "Data quality", ShieldCheck],
  ["/fpo/farmers/segments", "Segments", Layers],
  ["/fpo/seasons", "Seasons", CalendarDays],
  ["/fpo/tasks", "Tasks", ListTodo],
  ["/fpo/monitoring/rules", "Alert rules", SlidersHorizontal],
  ["/fpo/advisories", "Advisories", MessageCircle],
  ["/fpo/inputs", "Input planning", Sprout],
  ["/fpo/forecasts", "Forecasts", BarChart3],
  ["/fpo/reports/advanced", "Advanced reports", FileOutput],
  ["/fpo/commercial", "Commercial", BriefcaseBusiness],
  ["/fpo/operations", "Lots & inventory", PackageCheck],
  ["/fpo/execution", "Orders & logistics", Route],
  ["/fpo/compliance", "Compliance", FileCheck],
  ["/fpo/integrations", "Integrations", PlugZap],
  ["/fpo/profile", "Profile", UserRound],
];

export default function FpoSidebar() {
  const { entitlements } = useFpoPortal();
  const featureByRoute = { "/fpo/imports": "BULK_FARM_REGISTRATION", "/fpo/data-quality": "DATA_QUALITY_WORKBENCH", "/fpo/farmers/segments": "FARMER_SEGMENTATION", "/fpo/seasons": "SEASON_PLANNING", "/fpo/tasks": "FIELD_ACTIVITY_PLANNING", "/fpo/monitoring/rules": "ALERT_RULE_MANAGEMENT", "/fpo/advisories": "ADVISORY_WORKBENCH", "/fpo/inputs": "INPUT_REQUIREMENT_PLANNING", "/fpo/forecasts": "YIELD_FORECASTS_STANDARD", "/fpo/reports/advanced": "ADVANCED_REPORTS", "/fpo/commercial": "BUYER_EXPORTER_CRM", "/fpo/operations": "PRODUCE_AGGREGATION_LOTS", "/fpo/execution": "CONTRACT_AND_ORDER_MANAGEMENT", "/fpo/compliance": "COMPLIANCE_AND_CERTIFICATIONS", "/fpo/integrations": "ENTERPRISE_API_ACCESS" };
  const visible = items.filter(([to]) => !featureByRoute[to] || entitlements?.[featureByRoute[to]]?.enabled);
  return <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block"><div className="border-b border-slate-100 px-6 py-5"><p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-700">MaatiTrace</p><p className="mt-1 text-lg font-black text-slate-950">FPO Portal</p></div><nav className="space-y-1 p-4">{visible.map(([to, label, _Icon]) => { const ItemIcon = _Icon; return <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50"}`}><ItemIcon className="h-4 w-4" />{label}</NavLink>; })}</nav></aside>;
}
