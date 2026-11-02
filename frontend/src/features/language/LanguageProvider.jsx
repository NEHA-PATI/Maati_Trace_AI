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
    || LOCALES.EN;
}

export function LanguageProvider({ children }) {
  const { user } = useAuth();
  const [locale, setLocaleState] = useState(() => initialLocale(user));

  const setLocale = useCallback((nextLocale) => {
    const next = persistLocale(nextLocale);
    setLocaleState(next);
  }, []);

  useEffect(() => {
    const normalized = normalizeLocale(locale) || LOCALES.EN;
    document.documentElement.lang = normalized;
    document.documentElement.dir = "ltr";
    document.documentElement.dataset.locale = normalized;
  }, [locale]);

  useEffect(() => {
    function handleStorage(event) {
      if (event.key !== LANGUAGE_STORAGE_KEY && event.key !== LEGACY_LANGUAGE_STORAGE_KEY) return;
      const next = normalizeLocale(event.newValue);
      if (next && next !== locale) setLocaleState(next);
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
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
  // A small fallback keeps leaf components and unit tests renderable without
  // the application shell. The app itself always mounts the provider.
  return value || {
    locale: LOCALES.EN,
    setLocale: () => {},
    locales: [LOCALES.EN, LOCALES.OR],
    currentLanguageLabel: "English",
    isOdia: false,
  };
}

export function getActiveLocale() {
  return readStoredLocale() || LOCALES.EN;
}

export { LANGUAGE_STORAGE_KEY, LEGACY_LANGUAGE_STORAGE_KEY };
