export const LOCALES = Object.freeze({
  EN: "en",
  OR: "or",
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
  const next = normalizeLocale(locale) || LOCALES.EN;
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, next);
    // Keep the crop feature and older sessions in sync during migration.
    localStorage.setItem(LEGACY_LANGUAGE_STORAGE_KEY, next);
  } catch {
    // The provider retains the in-memory value when storage is unavailable.
  }
  return next;
}
