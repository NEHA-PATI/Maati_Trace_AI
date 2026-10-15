import { NavLink } from "react-router-dom";
import { useFpoPortal } from "./FpoPortalContext";
import { useTranslation } from "@/features/i18n";
import { Bell, FileText, LayoutDashboard, Map, Users, UserRound, UploadCloud, ShieldCheck, Layers, CalendarDays, ListTodo, SlidersHorizontal, MessageCircle, Sprout, BarChart3, FileOutput, BriefcaseBusiness, PackageCheck, Route, FileCheck, PlugZap, Link2, MapPinned } from "lucide-react";

const items = [
  ["/fpo/overview", "Overview", LayoutDashboard, "text-emerald-600"],
  ["/fpo/profile", "Profile", UserRound, "text-slate-500"],
  ["/fpo/farmers", "Farmers", Users, "text-indigo-500"],
  ["/fpo/farms", "Farms", Map, "text-blue-500"],
  ["/fpo/relationships", "Farm requests", Link2, "text-sky-500"],
  ["/fpo/monitoring", "Monitoring", Map, "text-cyan-500"],
  ["/fpo/alerts", "Alerts", Bell, "text-rose-500"],
  ["/fpo/reports", "Reports", FileText, "text-violet-500"],
  ["/fpo/imports", "Bulk onboarding", UploadCloud, "text-amber-500"],
  ["/fpo/geography", "Area performance", MapPinned],
  ["/fpo/data-quality", "Data quality", ShieldCheck, "text-teal-500"],
  ["/fpo/farmers/segments", "Segments", Layers, "text-fuchsia-500"],
  ["/fpo/seasons", "Seasons", CalendarDays, "text-orange-500"],
  ["/fpo/tasks", "Tasks", ListTodo, "text-blue-500"],
  ["/fpo/monitoring/rules", "Alert rules", SlidersHorizontal, "text-slate-500"],
  ["/fpo/advisories", "Advisories", MessageCircle, "text-emerald-500"],
  ["/fpo/inputs", "Input planning", Sprout, "text-lime-600"],
  ["/fpo/forecasts", "Forecasts", BarChart3, "text-blue-500"],
  ["/fpo/reports/advanced", "Advanced reports", FileOutput, "text-violet-500"],
  ["/fpo/commercial", "Commercial", BriefcaseBusiness, "text-amber-600"],
  ["/fpo/operations", "Lots & inventory", PackageCheck, "text-orange-500"],
  ["/fpo/execution", "Orders & logistics", Route, "text-cyan-600"],
  ["/fpo/compliance", "Compliance", FileCheck, "text-teal-600"],
  ["/fpo/integrations", "Integrations", PlugZap, "text-indigo-500"],
];

const FPO_LABELS = {
  Overview: { en: "Overview", or: "ସାରାଂଶ" }, Farmers: { en: "Farmers", or: "ଚାଷୀମାନେ" },
  Farms: { en: "Farms", or: "ଜମି" }, "Farm requests": { en: "Farm requests", or: "ଜମି ଅନୁରୋଧ" },
  Monitoring: { en: "Monitoring", or: "ନିରୀକ୍ଷଣ" }, "Area performance": { en: "Area performance", or: "ଅଞ୍ଚଳ ପ୍ରଦର୍ଶନ" },
  "Crops & seasons": { en: "Crops & seasons", or: "ଫସଲ ଏବଂ ଋତୁ" }, Alerts: { en: "Alerts", or: "ସତର୍କ ସୂଚନା" },
  Reports: { en: "Reports", or: "ରିପୋର୍ଟ" }, "Bulk onboarding": { en: "Bulk onboarding", or: "ଏକାଧିକ ପଞ୍ଜୀକରଣ" },
  "Data quality": { en: "Data quality", or: "ତଥ୍ୟର ଗୁଣବତ୍ତା" }, Segments: { en: "Segments", or: "ବିଭାଗ" },
  Seasons: { en: "Seasons", or: "ଋତୁ" }, Tasks: { en: "Tasks", or: "କାର୍ଯ୍ୟ" }, "Alert rules": { en: "Alert rules", or: "ସତର୍କତା ନିୟମ" },
  Advisories: { en: "Advisories", or: "ପରାମର୍ଶ" }, "Input planning": { en: "Input planning", or: "ଉପକରଣ ଯୋଜନା" },
  Forecasts: { en: "Forecasts", or: "ପୂର୍ବାନୁମାନ" }, "Advanced reports": { en: "Advanced reports", or: "ଉନ୍ନତ ରିପୋର୍ଟ" },
  Commercial: { en: "Commercial", or: "ବାଣିଜ୍ୟିକ" }, "Lots & inventory": { en: "Lots & inventory", or: "ଲଟ୍ ଏବଂ ମହଜୁଦ" },
  "Orders & logistics": { en: "Orders & logistics", or: "ଅର୍ଡର ଏବଂ ପରିବହନ" }, Compliance: { en: "Compliance", or: "ଅନୁପାଳନ" },
  Integrations: { en: "Integrations", or: "ସଂଯୋଜନ" }, Profile: { en: "Profile", or: "ପ୍ରୋଫାଇଲ୍" },
};

export default function FpoSidebar() {
  const { entitlements } = useFpoPortal();
  const { locale, t } = useTranslation();
  const featureByRoute = { "/fpo/imports": "BULK_FARM_REGISTRATION", "/fpo/data-quality": "DATA_QUALITY_WORKBENCH", "/fpo/farmers/segments": "FARMER_SEGMENTATION", "/fpo/seasons": "SEASON_PLANNING", "/fpo/tasks": "FIELD_ACTIVITY_PLANNING", "/fpo/monitoring/rules": "ALERT_RULE_MANAGEMENT", "/fpo/advisories": "ADVISORY_WORKBENCH", "/fpo/inputs": "INPUT_REQUIREMENT_PLANNING", "/fpo/forecasts": "YIELD_FORECASTS_STANDARD", "/fpo/reports/advanced": "ADVANCED_REPORTS", "/fpo/commercial": "BUYER_EXPORTER_CRM", "/fpo/operations": "PRODUCE_AGGREGATION_LOTS", "/fpo/execution": "CONTRACT_AND_ORDER_MANAGEMENT", "/fpo/compliance": "COMPLIANCE_AND_CERTIFICATIONS", "/fpo/integrations": "ENTERPRISE_API_ACCESS" };
  const visible = items.filter(([to]) => !featureByRoute[to] || entitlements?.[featureByRoute[to]]?.enabled);
  return <aside className="fixed bottom-4 left-0 top-0 z-40 hidden w-64 overflow-hidden rounded-r-2xl border-r border-slate-200 bg-white shadow-sm lg:block"><div className="border-b border-slate-100 bg-gradient-to-br from-emerald-50 to-white px-5 py-5"><p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-700">MaatiTrace</p><p className="mt-1 text-lg font-black text-slate-950">{t("profilePortal")}</p></div><nav aria-label="FPO sections" className="h-[calc(100%-88px)] space-y-1 overflow-y-auto p-3 [scrollbar-width:thin]">{visible.map(([to, label, _Icon, iconClass]) => { const ItemIcon = _Icon; const copy = FPO_LABELS[label]; return <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-bold transition-colors ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}><ItemIcon className={`h-4 w-4 ${iconClass || "text-slate-500"}`} />{copy ? (locale === "or-IN" ? copy.or : copy.en) : label}</NavLink>; })}</nav></aside>;
}
