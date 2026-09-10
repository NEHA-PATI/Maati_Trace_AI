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
        "flex min-h-[84px] w-full items-center gap-3 rounded-2xl border border-[#E9E7DC] bg-[#FBFAF7] px-3 py-3 text-left transition active:scale-[0.99]",
        "hover:border-[#C9D8BD] disabled:cursor-not-allowed disabled:opacity-60",
      )}
    >
      <div className="grid h-[60px] w-[60px] shrink-0 place-items-center overflow-hidden rounded-xl bg-[linear-gradient(150deg,#B7D09E,#7FA66A)] text-white">
        {crop.image_url ? (
          <img src={systemMediaUrl(crop.image_url)} alt="" loading="lazy" className="h-full w-full object-cover" />
        ) : (
          <CropIcon className="h-8 w-8" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <Bilingual as="div" className="truncate text-[15px] font-black text-[#1D2117]" primaryText={crop.name} />
        <p className="mt-0.5 truncate text-xs font-medium text-[#5B6055]">{crop.lifecycle_type === "PERENNIAL" ? (locale === "or-IN" ? "ବହୁବର୍ଷୀୟ ଫସଲ" : "Perennial crop") : (locale === "or-IN" ? "ଋତୁକାଳୀନ ଫସଲ" : "Seasonal crop")}</p>
        {attached ? (
          <span className="mt-1.5 inline-flex rounded-full bg-[#E1F1D6] px-2.5 py-0.5 text-xs font-black text-[#33492A]">
            {primary(STRINGS.active, locale)}
          </span>
        ) : null}
      </div>
      {disabled ? (
        <Loader2 className="h-5 w-5 shrink-0 animate-spin text-[#4B6B3A]" />
      ) : (
        <ChevronRight className="h-5 w-5 shrink-0 text-[#5B6055]" />
      )}
    </button>
  );
}

export default memo(CropCard);
