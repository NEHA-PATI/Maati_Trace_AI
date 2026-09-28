import { useLanguage } from "@/features/language";
import { LEGACY_LANGUAGE_STORAGE_KEY } from "@/features/language";

export function hasStoredCropLocale() {
  try {
    return Boolean(localStorage.getItem(LEGACY_LANGUAGE_STORAGE_KEY));
  } catch {
    return false;
  }
}

/** Per-viewer UI preference only (which language the crop diary displays
 * in) — not authentication state, so plain localStorage is fine here. */
export function useLocale() {
  const { locale, setLocale } = useLanguage();
  return [locale, setLocale];
}
