import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/features/auth/context/useAuth";
import {
  LANGUAGE_STORAGE_KEY,
  LEGACY_LANGUAGE_STORAGE_KEY,
  LOCALES,
  localeLabel,
  normalizeLocale,
  persistLocale,
  readStoredLocale,
} from "./language";

const LanguageContext = createContext(null);

function browserLocale() {
  if (typeof navigator === "undefined") return null;
  return normalizeLocale(navigator.language);
}

function initialLocale(user) {
  return readStoredLocale()
    || normalizeLocale(user?.preferred_language)
    || browserLocale()
    || LOCALES.OR;
}

export function LanguageProvider({ children }) {
  const { user } = useAuth();
  const [locale, setLocaleState] = useState(() => initialLocale(user));

  const setLocale = useCallback((nextLocale) => {
    const next = persistLocale(nextLocale);
    setLocaleState(next);
  }, []);

  useEffect(() => {
    const normalized = normalizeLocale(locale) || LOCALES.OR;
    document.documentElement.lang = normalized === LOCALES.OR ? "or" : "en-IN";
    document.documentElement.dir = "ltr";
  }, [locale]);

  useEffect(() => {
    // A saved browser choice always wins over profile bootstrap. This prevents
    // a late auth response from undoing a choice made in the current session.
    if (readStoredLocale()) return;
    const profileLocale = normalizeLocale(user?.preferred_language);
    if (profileLocale && profileLocale !== locale) setLocaleState(profileLocale);
  }, [user?.preferred_language, locale]);

  const value = useMemo(() => ({
    locale,
    setLocale,
    locales: [LOCALES.EN, LOCALES.OR],
    currentLanguageLabel: localeLabel(locale),
    isOdia: locale === LOCALES.OR,
  }), [locale, setLocale]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const value = useContext(LanguageContext);
  if (!value) throw new Error("useLanguage must be used inside LanguageProvider");
  return value;
}

export function getActiveLocale() {
  return readStoredLocale() || LOCALES.OR;
}

export { LANGUAGE_STORAGE_KEY, LEGACY_LANGUAGE_STORAGE_KEY };
