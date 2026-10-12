import { memo } from "react";
import { ChevronRight, Loader2 } from "lucide-react";

import { systemMediaUrl } from "@/features/crop-observation/api/cropObservationApi";
import Bilingual from "@/features/crop-observation/components/Bilingual";
import { iconForPractice } from "@/features/crop-observation/components/fieldIcons";
import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

function CropCard({ crop, attached, onSelect, onPrefetch, disabled, locale }) {
  const CropIcon = iconForPractice(crop.crop_code === "coconut" ? "orchard_management" : "seed_management");

  return (
    <button
      type="button"
      onClick={() => onSelect(crop)}
      onPointerEnter={onPrefetch}
      onFocus={onPrefetch}
      disabled={disabled}
      className={cn(
        "group relative flex min-h-[132px] w-full items-center gap-5 rounded-[24px] border border-[#E5E8DF] bg-white px-5 py-5 text-left shadow-[0_5px_18px_rgba(43,61,35,0.04)] transition duration-200 active:scale-[0.99]",
        "hover:-translate-y-0.5 hover:border-[#B8CEA9] hover:shadow-[0_12px_28px_rgba(43,61,35,0.10)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#71985C] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
      )}
    >
      <div className="grid h-[82px] w-[82px] shrink-0 place-items-center overflow-hidden rounded-[20px] bg-[linear-gradient(150deg,#BED6A7,#78A460)] text-white shadow-inner">
        {crop.image_url ? (
          <img src={systemMediaUrl(crop.image_url)} alt="" loading="lazy" className="h-full w-full object-cover" />
        ) : (
          <CropIcon className="h-10 w-10" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <Bilingual as="div" className="truncate text-[16px] font-black tracking-[-0.01em] text-[#1D2117]" primaryText={crop.name} />
        <p className="mt-1 truncate text-[13px] font-medium text-[#687064]">{crop.lifecycle_type === "PERENNIAL" ? (locale === "or-IN" ? "ବହୁବର୍ଷୀୟ ଫସଲ" : "Perennial crop") : (locale === "or-IN" ? "ଋତୁକାଳୀନ ଫସଲ" : "Seasonal crop")}</p>
        {attached ? (
          <span className="mt-2 inline-flex rounded-full bg-[#E8F3E0] px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-[#426333]">
            {primary(STRINGS.active, locale)}
          </span>
        ) : null}
      </div>
      {disabled ? (
        <Loader2 className="h-5 w-5 shrink-0 animate-spin text-[#4B6B3A]" />
      ) : (
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-[#E2E8DD] bg-[#F7FAF4] text-[#60705A] transition group-hover:border-[#B8CEA9] group-hover:bg-[#EAF3E4] group-hover:text-[#426333]"><ChevronRight className="h-5 w-5" /></span>
      )}
    </button>
  );
}

export default memo(CropCard);
