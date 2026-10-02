import { NavLink } from "react-router-dom";
import { useFpoPortal } from "./FpoPortalContext";
import { useTranslation } from "@/features/i18n";
import { Bell, FileText, LayoutDashboard, Map, Users, UserRound, UploadCloud, ShieldCheck, Layers, CalendarDays, ListTodo, SlidersHorizontal, MessageCircle, Sprout, BarChart3, FileOutput, BriefcaseBusiness, PackageCheck, Route, FileCheck, PlugZap, Link2, MapPinned } from "lucide-react";

const items = [
  ["/fpo/overview", "Overview", LayoutDashboard],
  ["/fpo/farmers", "Farmers", Users],
  ["/fpo/farms", "Farms", Map],
  ["/fpo/relationships", "Farm requests", Link2],
  ["/fpo/monitoring", "Monitoring", Map],
  ["/fpo/geography", "Area performance", MapPinned],
  ["/fpo/crops", "Crops & seasons", Sprout],
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
  return <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block"><div className="border-b border-slate-100 px-6 py-5"><p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-700">MaatiTrace</p><p className="mt-1 text-lg font-black text-slate-950">{t("profilePortal")}</p></div><nav className="space-y-1 p-4">{visible.map(([to, label, _Icon]) => { const ItemIcon = _Icon; const copy = FPO_LABELS[label]; return <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50"}`}><ItemIcon className="h-4 w-4" />{copy ? (locale === "or-IN" ? copy.or : copy.en) : label}</NavLink>; })}</nav></aside>;
}
