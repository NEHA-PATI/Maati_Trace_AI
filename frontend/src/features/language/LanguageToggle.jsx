import { Globe2 } from "lucide-react";

import { useLanguage } from "./LanguageProvider";
import { languageString, LOCALES } from "./language";

export default function LanguageToggle({ compact = false, className = "" }) {
  const { locale, setLocale } = useLanguage();
  const nextLocale = locale === LOCALES.OR ? LOCALES.EN : LOCALES.OR;
  const label = languageString(locale === LOCALES.OR ? "switchToEnglish" : "switchToOdia", locale);

  return (
    <button
      type="button"
      onClick={() => setLocale(nextLocale)}
      aria-label={`${languageString("language", locale)}: ${label}`}
      title={`${languageString("language", locale)}: ${label}`}
      className={`inline-flex h-10 items-center justify-center gap-2 rounded-full border border-[var(--mt-line)] bg-white px-3 text-[13px] font-bold text-[var(--mt-ink-soft)] transition-colors hover:bg-[var(--mt-paper-warm)] ${compact ? "w-10 px-0" : ""} ${className}`}
    >
      <Globe2 className="h-4 w-4 text-[var(--mt-leaf)]" aria-hidden="true" />
      <span className={compact ? "sr-only" : ""}>{label}</span>
    </button>
  );
}
