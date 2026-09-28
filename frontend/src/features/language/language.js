export const LOCALES = Object.freeze({
  EN: "en-IN",
  OR: "or-IN",
});

export const SUPPORTED_LOCALES = Object.freeze([LOCALES.EN, LOCALES.OR]);
export const LANGUAGE_STORAGE_KEY = "maatitrace_locale";
export const LEGACY_LANGUAGE_STORAGE_KEY = "maatitrace_crop_locale";

export function normalizeLocale(value) {
  if (!value) return null;
  const normalized = String(value).toLowerCase();
  if (normalized === "en" || normalized === "en-in") return LOCALES.EN;
  if (normalized === "or" || normalized === "or-in" || normalized === "od") return LOCALES.OR;
  return null;
}

export function localeToProfileLanguage(locale) {
  return normalizeLocale(locale) === LOCALES.OR ? "or" : "en";
}

export function localeLabel(locale) {
  return normalizeLocale(locale) === LOCALES.OR ? "ଓଡ଼ିଆ" : "English";
}

export function readStoredLocale() {
  try {
    return normalizeLocale(localStorage.getItem(LANGUAGE_STORAGE_KEY))
      || normalizeLocale(localStorage.getItem(LEGACY_LANGUAGE_STORAGE_KEY));
  } catch {
    return null;
  }
}

export function persistLocale(locale) {
  const next = normalizeLocale(locale) || LOCALES.OR;
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, next);
    // Keep the crop feature and older sessions in sync during migration.
    localStorage.setItem(LEGACY_LANGUAGE_STORAGE_KEY, next);
  } catch {
    // The provider retains the in-memory value when storage is unavailable.
  }
  return next;
}

export const LANGUAGE_STRINGS = Object.freeze({
  switchToEnglish: { en: "English", or: "ଇଂରାଜୀ" },
  switchToOdia: { en: "ଓଡ଼ିଆ", or: "ଓଡ଼ିଆ" },
  language: { en: "Language", or: "ଭାଷା" },
  notifications: { en: "Notifications", or: "ବିଜ୍ଞପ୍ତି" },
  logout: { en: "Log out", or: "ଲଗ୍ ଆଉଟ୍" },
  loggingOut: { en: "Logging out…", or: "ଲଗ୍ ଆଉଟ୍ ହେଉଛି…" },
  home: { en: "Home", or: "ମୁଖ୍ୟ ପୃଷ୍ଠା" },
  ourMethod: { en: "Our Method", or: "ଆମ ପଦ୍ଧତି" },
  useCases: { en: "Use Cases", or: "ବ୍ୟବହାର କ୍ଷେତ୍ର" },
  plans: { en: "Plans", or: "ଯୋଜନା" },
});

export function languageString(key, locale) {
  const value = LANGUAGE_STRINGS[key];
  if (!value) return key;
  return (normalizeLocale(locale) === LOCALES.OR ? value.or : value.en) || value.en;
}
