import { useLanguage } from "@/features/language/LanguageProvider";
import { translate } from "./catalogue";
import { LOCALES, normalizeLocale } from "@/features/language/language";

export { UI_STRINGS, translate, useLocaleText } from "./catalogue";

export function useTranslation() {
  const { locale } = useLanguage();
  return {
    locale,
    t: (key, options) => translate(key, locale, options),
  };
}

export function locationLabel(value, locale) {
  if (!value || typeof value !== "object") return value;
  return normalizeLocale(locale) === LOCALES.OR ? value.or || value.en : value.en || value.or;
}

export function apiErrorMessage(error, t) {
  const key = error?.code === "INVALID_CREDENTIALS"
    ? "errors.invalidCredentials"
    : error?.code === "REQUEST_TIMEOUT"
      ? "errors.requestTimeout"
      : error?.code === "NETWORK_ERROR"
        ? "errors.network"
        : "errors.requestFailed";
  return t(key);
}

export function validationMessage(message, t) {
  const keys = {
    "Enter your email or mobile number.": "validation.emailOrPhone",
    "Enter your password.": "validation.password",
  };
  return keys[message] ? t(keys[message]) : message;
}
