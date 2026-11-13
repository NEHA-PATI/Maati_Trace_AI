import {
  BarChart3,
  Bell,
  CloudLightning,
  BriefcaseBusiness,
  CalendarDays,
  FileCheck,
  FileOutput,
  FileText,
  LayoutDashboard,
  Layers,
  Link2,
  ListTodo,
  Map,
  MapPinned,
  MessageCircle,
  PackageCheck,
  PlugZap,
  Route,
  ShieldCheck,
  SlidersHorizontal,
  Sprout,
  UploadCloud,
  UserRound,
  Users,
} from "lucide-react";

export const FPO_NAV_GROUPS = [
  {
    label: "Workspace",
    items: [
      { to: "/fpo/overview", label: "Overview", icon: LayoutDashboard, feature: "BASIC_REPORTS", shortcut: true },
      { to: "/fpo/farmers", label: "Farmers", icon: Users, shortcut: true },
      { to: "/fpo/relationships", label: "Farm requests", icon: Link2 },
      { to: "/fpo/monitoring", label: "Monitoring", icon: Map, feature: "FARM_MAP", shortcut: true },
      { to: "/fpo/alerts", label: "Alerts", icon: Bell, feature: "BASIC_ALERTS", shortcut: true },
    ],
  },
  {
    label: "Insights",
    items: [
      { to: "/fpo/geography", label: "Area performance", icon: MapPinned, feature: "BASIC_REPORTS" },
      { to: "/fpo/crops", label: "Crop performance", icon: Sprout, feature: "BASIC_REPORTS" },
      { to: "/fpo/reports", label: "Reports", icon: FileText, feature: "BASIC_REPORTS" },
      { to: "/fpo/natural-disasters", label: "Natural disasters", icon: CloudLightning, feature: "FARM_MAP" },
    ],
  },
  {
    label: "Planning & fieldwork",
    items: [
      { to: "/fpo/imports", label: "Bulk onboarding", icon: UploadCloud, feature: "BULK_FARM_REGISTRATION" },
      { to: "/fpo/data-quality", label: "Data quality", icon: ShieldCheck, feature: "DATA_QUALITY_WORKBENCH" },
      { to: "/fpo/farmers/segments", label: "Segments", icon: Layers, feature: "FARMER_SEGMENTATION" },
      { to: "/fpo/seasons", label: "Seasons", icon: CalendarDays, feature: "SEASON_PLANNING" },
      { to: "/fpo/tasks", label: "Tasks", icon: ListTodo, feature: "FIELD_ACTIVITY_PLANNING" },
      { to: "/fpo/monitoring/rules", label: "Alert rules", icon: SlidersHorizontal, feature: "PORTFOLIO_MONITORING_ADVANCED" },
      { to: "/fpo/advisories", label: "Advisories", icon: MessageCircle, feature: "ADVISORY_WORKBENCH" },
      { to: "/fpo/inputs", label: "Input planning", icon: Sprout, feature: "INPUT_REQUIREMENT_PLANNING" },
      { to: "/fpo/forecasts", label: "Forecasts", icon: BarChart3, feature: "YIELD_FORECASTS_STANDARD" },
      { to: "/fpo/reports/advanced", label: "Advanced reports", icon: FileOutput, feature: "ADVANCED_REPORTS" },
    ],
  },
  {
    label: "Commercial & supply",
    items: [
      { to: "/fpo/commercial", label: "Commercial", icon: BriefcaseBusiness, feature: "BUYER_EXPORTER_CRM" },
      { to: "/fpo/operations", label: "Lots & inventory", icon: PackageCheck, feature: "PRODUCE_AGGREGATION_LOTS" },
      { to: "/fpo/execution", label: "Orders & logistics", icon: Route, feature: "CONTRACT_AND_ORDER_MANAGEMENT" },
    ],
  },
  {
    label: "Governance",
    items: [
      { to: "/fpo/compliance", label: "Compliance", icon: FileCheck, feature: "COMPLIANCE_AND_CERTIFICATIONS" },
      { to: "/fpo/integrations", label: "Integrations", icon: PlugZap, feature: "ENTERPRISE_API_ACCESS" },
    ],
  },
  {
    label: "Account",
    items: [{ to: "/fpo/profile", label: "Profile", icon: UserRound }],
  },
];

export function getVisibleFpoNavGroups(entitlements = {}) {
  return FPO_NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter(
      ({ feature }) => !feature || entitlements?.[feature]?.enabled,
    ),
  })).filter((group) => group.items.length > 0);
}
