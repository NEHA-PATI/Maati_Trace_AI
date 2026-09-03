import { memo } from "react";
import { ChevronRight } from "lucide-react";

import { systemMediaUrl } from "@/features/crop-observation/api/cropObservationApi";
import Bilingual from "@/features/crop-observation/components/Bilingual";
import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

function CropCard({ crop, attached, onSelect, onPrefetch, disabled, locale }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(crop)}
      onPointerEnter={onPrefetch}
      onFocus={onPrefetch}
      disabled={disabled}
      className={cn(
        "flex min-h-[76px] w-full items-center gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left shadow-sm transition active:scale-[0.99]",
        "hover:border-emerald-300 disabled:cursor-not-allowed disabled:opacity-60",
      )}
    >
      <div className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-xl bg-emerald-50 text-2xl">
        {crop.image_url ? (
          <img src={systemMediaUrl(crop.image_url)} alt="" loading="lazy" className="h-full w-full object-cover" />
        ) : (
          "🌾"
        )}
      </div>
      <Bilingual
        as="div"
        className="min-w-0 flex-1 text-base font-bold text-slate-950"
        primaryText={crop.name}
      />
      {attached ? (
        <span className="shrink-0 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
          {primary(STRINGS.active, locale)}
        </span>
      ) : (
        <ChevronRight className="h-5 w-5 shrink-0 text-slate-300" />
      )}
    </button>
  );
}

export default memo(CropCard);
