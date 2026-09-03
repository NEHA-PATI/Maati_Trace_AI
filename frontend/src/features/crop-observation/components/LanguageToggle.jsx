import { Globe2 } from "lucide-react";

import { LOCALES } from "@/features/crop-observation/i18n";

export default function LanguageToggle({ locale, setLocale }) {
  const nextLocale = locale === LOCALES.OR ? LOCALES.EN : LOCALES.OR;
  const label = locale === LOCALES.OR ? "English" : "Odia";

  return (
    <button
      type="button"
      onClick={() => setLocale(nextLocale)}
      aria-label={`Switch to ${label}`}
      className="inline-flex h-11 items-center gap-2 rounded-[14px] border border-[#E9E7DC] bg-[#F7F8F3] px-3 text-sm font-bold text-[#1D2117] shadow-sm active:scale-[0.98]"
    >
      <Globe2 className="h-4 w-4 text-[#4B6B3A]" />
      {label}
    </button>
  );
}
