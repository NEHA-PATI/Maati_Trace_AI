import { Languages } from "lucide-react";

import { LOCALES } from "@/features/crop-observation/i18n";

/** Compact ଓଡ଼ିଆ ⇄ EN switch used in every crop-diary header. */
export default function LanguageToggle({ locale, setLocale }) {
  const next = locale === LOCALES.OR ? LOCALES.EN : LOCALES.OR;
  return (
    <button
      type="button"
      onClick={() => setLocale(next)}
      aria-label={locale === LOCALES.OR ? "Switch to English" : "ଓଡ଼ିଆକୁ ବଦଳାନ୍ତୁ"}
      className="flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 active:bg-slate-100"
    >
      <Languages className="h-3.5 w-3.5" />
      {locale === LOCALES.OR ? "EN" : "ଓଡ଼ିଆ"}
    </button>
  );
}
