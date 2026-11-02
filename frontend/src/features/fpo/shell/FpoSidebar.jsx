import { NavLink } from "react-router-dom";
import { useTranslation } from "@/features/i18n";
import { useFpoPortal } from "./FpoPortalContext";
import { getVisibleFpoNavGroups } from "./fpoNavigation";

const FPO_LABELS = {
  Overview: { en: "Overview", or: "ସାରାଂଶ" },
  Farmers: { en: "Farmers", or: "ଚାଷୀମାନେ" },
  "Farm requests": { en: "Farm requests", or: "ଜମି ଅନୁରୋଧ" },
  Monitoring: { en: "Monitoring", or: "ନିରୀକ୍ଷଣ" },
  "Area performance": { en: "Area performance", or: "ଅଞ୍ଚଳ ପ୍ରଦର୍ଶନ" },
  "Crop performance": { en: "Crop performance", or: "ଫସଲ ପ୍ରଦର୍ଶନ" },
  Alerts: { en: "Alerts", or: "ସତର୍କ ସୂଚନା" },
  Reports: { en: "Reports", or: "ରିପୋର୍ଟ" },
  "Bulk onboarding": { en: "Bulk onboarding", or: "ଏକାଧିକ ପଞ୍ଜୀକରଣ" },
  "Data quality": { en: "Data quality", or: "ତଥ୍ୟର ଗୁଣବତ୍ତା" },
  Segments: { en: "Segments", or: "ବିଭାଗ" },
  Seasons: { en: "Seasons", or: "ଋତୁ" },
  Tasks: { en: "Tasks", or: "କାର୍ଯ୍ୟ" },
  "Alert rules": { en: "Alert rules", or: "ସତର୍କତା ନିୟମ" },
  Advisories: { en: "Advisories", or: "ପରାମର୍ଶ" },
  "Input planning": { en: "Input planning", or: "ଉପକରଣ ଯୋଜନା" },
  Forecasts: { en: "Forecasts", or: "ପୂର୍ବାନୁମାନ" },
  "Advanced reports": { en: "Advanced reports", or: "ଉନ୍ନତ ରିପୋର୍ଟ" },
  Commercial: { en: "Commercial", or: "ବାଣିଜ୍ୟିକ" },
  "Lots & inventory": { en: "Lots & inventory", or: "ଲଟ୍ ଏବଂ ମହଜୁଦ" },
  "Orders & logistics": { en: "Orders & logistics", or: "ଅର୍ଡର ଏବଂ ପରିବହନ" },
  Compliance: { en: "Compliance", or: "ଅନୁପାଳନ" },
  Integrations: { en: "Integrations", or: "ସଂଯୋଜନ" },
  Profile: { en: "Profile", or: "ପ୍ରୋଫାଇଲ୍" },
};

export default function FpoSidebar() {
  const { entitlements } = useFpoPortal();
  const { locale, t } = useTranslation();
  const groups = getVisibleFpoNavGroups(entitlements);

  return (
    <aside className="fixed bottom-4 left-0 top-0 z-40 hidden w-64 overflow-hidden rounded-r-2xl border-r border-slate-200 bg-white shadow-sm lg:block">
      <div className="border-b border-slate-100 bg-gradient-to-br from-emerald-50 to-white px-5 py-5">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-700">MaatiTrace</p>
        <p className="mt-1 text-lg font-black text-slate-950">{t("profilePortal")}</p>
      </div>
      <nav aria-label="FPO sections" className="h-[calc(100%-88px)] space-y-4 overflow-y-auto p-3 [scrollbar-width:thin]">
        {groups.map((group) => (
          <section key={group.label} aria-label={group.label}>
            <h2 className="px-3 pb-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">{group.label}</h2>
            <div className="space-y-1">
              {group.items.map(({ to, label, icon: Icon }) => {
                const ItemIcon = Icon;
                const copy = FPO_LABELS[label];
                return (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === "/fpo/overview"}
                    className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold transition-colors ${isActive ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}
                  >
                    <ItemIcon className="h-4 w-4 shrink-0 text-slate-500" />
                    {copy ? (locale === "or-IN" ? copy.or : copy.en) : label}
                  </NavLink>
                );
              })}
            </div>
          </section>
        ))}
      </nav>
    </aside>
  );
}
