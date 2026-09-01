import { useCallback, useState } from "react";

const STORAGE_KEY = "maatitrace_crop_locale";

function readStoredLocale() {
  try {
    return localStorage.getItem(STORAGE_KEY) || "or-IN";
  } catch {
    return "or-IN";
  }
}

/** Per-viewer UI preference only (which language the crop diary displays
 * in) — not authentication state, so plain localStorage is fine here. */
export function useLocale() {
  const [locale, setLocaleState] = useState(readStoredLocale);

  const setLocale = useCallback((next) => {
    setLocaleState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Private browsing / storage blocked — the in-memory state still works.
    }
  }, []);

  return [locale, setLocale];
}
