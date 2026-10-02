import { NavLink } from "react-router-dom";
import { useTranslation } from "@/features/i18n";

export default function FpoMobileNavigation() {
  const { t } = useTranslation();
  return <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-slate-200 bg-white p-2 lg:hidden">{[["/fpo/overview", "overview"], ["/fpo/farmers", "farmers"], ["/fpo/relationships", "requests"], ["/fpo/alerts", "alerts"], ["/fpo/profile", "profile"]].map(([to, key]) => <NavLink key={to} to={to} className={({ isActive }) => `rounded-lg py-2 text-center text-[11px] font-bold ${isActive ? "text-emerald-700" : "text-slate-500"}`}>{t(key)}</NavLink>)}</nav>;
}
