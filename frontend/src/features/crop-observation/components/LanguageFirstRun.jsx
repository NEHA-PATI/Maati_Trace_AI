import { ArrowRight, Check, MapPin } from "lucide-react";

import { LOCALES } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

const OPTIONS = [
  {
    locale: LOCALES.OR,
    label: "ଓଡ଼ିଆ",
    sideLabel: "Odia - default",
    title: "ଆପଣଙ୍କ ଭାଷା ବାଛନ୍ତୁ",
    cta: "ଆଗକୁ ବଢନ୍ତୁ",
  },
  {
    locale: LOCALES.EN,
    label: "English",
    sideLabel: "ଓଡ଼ିଆ",
    title: "Choose your language",
    cta: "Continue",
  },
];

export default function LanguageFirstRun({ locale, setLocale, onContinue }) {
  const active = OPTIONS.find((option) => option.locale === locale) || OPTIONS[0];

  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-[480px] flex-col bg-white px-10 pb-[calc(84px+env(safe-area-inset-bottom))] pt-12">
      <div className="flex flex-1 flex-col items-center text-center">
        <div className="grid h-[84px] w-[84px] place-items-center rounded-[24px] bg-[#4B6B3A] text-white">
          <MapPin className="h-11 w-11" strokeWidth={2.4} />
        </div>

        <h1 className="mt-7 text-[24px] font-black leading-tight text-[#1D2117]">{active.title}</h1>
        <p className="mt-2 max-w-[310px] text-[15px] font-medium leading-6 text-[#5B6055]">
          Choose your language. You can change this anytime from the top of any screen.
        </p>

        <div className="mt-9 w-full space-y-3">
          {OPTIONS.map((option) => {
            const selected = option.locale === locale;
            return (
              <button
                key={option.locale}
                type="button"
                onClick={() => setLocale(option.locale)}
                className={cn(
                  "flex min-h-16 w-full items-center justify-between rounded-2xl border-2 bg-white px-5 text-left transition active:scale-[0.99]",
                  selected ? "border-[#4B6B3A] bg-[#E7EEE1]" : "border-[#E7DFD3]",
                )}
              >
                <span className="text-lg font-black text-[#1D2117]">{option.label}</span>
                <span className="inline-flex items-center gap-1 text-sm font-medium text-[#5B6055]">
                  {selected ? <Check className="h-4 w-4 text-[#4B6B3A]" /> : null}
                  {option.sideLabel}
                </span>
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={onContinue}
          className="mt-5 flex h-[52px] w-full items-center justify-center gap-2 rounded-[14px] bg-[#4B6B3A] text-base font-black text-white shadow-sm active:scale-[0.99]"
        >
          <ArrowRight className="h-5 w-5" />
          {active.cta}
        </button>
      </div>
    </div>
  );
}
