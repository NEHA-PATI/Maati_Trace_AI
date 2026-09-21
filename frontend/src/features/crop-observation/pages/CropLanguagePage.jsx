import { Languages } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useLocale } from "@/features/crop-observation/hooks/useLocale";
import { LOCALES } from "@/features/crop-observation/i18n";

const OPTIONS = [
  {
    locale: LOCALES.OR,
    title: "ଓଡ଼ିଆ",
    subtitle: "ଓଡ଼ିଆରେ ଫସଲ ତଥ୍ୟ ଦିଅନ୍ତୁ",
  },
  {
    locale: LOCALES.EN,
    title: "English",
    subtitle: "Use crop updates in English",
  },
];

/**
 * Entry page for the My Crops feature.
 *
 * IMPORTANT ROUTING CONTRACT:
 * - navbar "My Crops" -> /my-crops/language
 * - choosing a language -> /my-crops
 * - Back from a crop stage -> /my-crops (does NOT force language selection)
 *
 * The selected locale is persisted by useLocale(), so every API request and
 * every farmer-facing label after this screen uses one language only.
 */
export default function CropLanguagePage() {
  const navigate = useNavigate();
  const [, setLocale] = useLocale();

  function choose(locale) {
    setLocale(locale);
    navigate("/my-crops", { replace: true });
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#F6F7F2] px-4 py-8 sm:px-6 lg:py-14">
      <div className="mx-auto flex min-h-[70vh] w-full max-w-[760px] flex-col justify-center">
        <div className="rounded-[28px] border border-[#E3E8DE] bg-white p-5 shadow-sm sm:p-8 lg:p-10">
          <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-[#4B6B3A] text-white">
            <Languages className="h-8 w-8" />
          </div>

          <div className="mt-5 text-center">
            <h1 className="text-2xl font-black text-[#1D2117] sm:text-3xl">
              Choose Language
            </h1>
            <p className="mt-1 text-xl font-bold text-[#4B6B3A] sm:text-2xl">
              ଭାଷା ବାଛନ୍ତୁ
            </p>
            <p className="mx-auto mt-3 max-w-[520px] text-sm font-medium leading-6 text-[#5B6055] sm:text-base">
              Select the language you want to use for crop updates.
            </p>
          </div>

          <div className="mt-7 grid gap-4 sm:grid-cols-2">
            {OPTIONS.map((option) => (
              <button
                key={option.locale}
                type="button"
                onClick={() => choose(option.locale)}
                className="group min-h-[150px] rounded-[22px] border-2 border-[#DCE5D4] bg-[#FBFCF8] p-5 text-left transition hover:border-[#4B6B3A] hover:bg-[#EEF4E9] active:scale-[0.99]"
              >
                <div className="text-2xl font-black text-[#1D2117]">{option.title}</div>
                <div className="mt-2 text-sm font-semibold leading-5 text-[#5B6055]">
                  {option.subtitle}
                </div>
                <div className="mt-5 inline-flex rounded-full bg-[#E1F1D6] px-3 py-1 text-xs font-black text-[#33492A]">
                  {option.locale === LOCALES.OR ? "ବାଛନ୍ତୁ" : "Choose"}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
