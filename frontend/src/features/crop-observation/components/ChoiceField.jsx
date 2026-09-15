import { iconForOption } from "./fieldIcons";
import { systemMediaUrl } from "@/features/crop-observation/api/cropObservationApi";

function gridClass(count) {
  if (count >= 4) return "grid-cols-4 gap-2";
  return "grid-cols-2 gap-2.5";
}

export default function ChoiceField({ field, value, onChange }) {
  const options = field.options || [];

  return (
    <div className={`grid ${gridClass(options.length)}`}>
      {options.map((option) => {
        const Icon = iconForOption(option.option_code, field);
        const compact = options.length >= 4;
        const selected = value === option.option_code;

        return (
          <button
            key={option.option_code}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(option.option_code)}
            className={`flex flex-col items-center justify-center rounded-[14px] border-2 bg-white text-center font-bold leading-tight transition active:scale-[0.98] ${
              compact ? "min-h-[66px] px-1.5 py-2 text-[11px]" : "min-h-[60px] px-2.5 py-2 text-sm"
            } ${
              selected
                ? "border-[#4B6B3A] bg-[#E1F1D6] text-[#33492A]"
                : "border-[#E9E7DC] text-[#1D2117] hover:border-[#C9D8BD]"
            }`}
          >
            {option.image_url ? (
              <img src={systemMediaUrl(option.image_url)} alt="" className="mb-2 h-16 w-full rounded-lg object-cover" loading="lazy" />
            ) : (
              <Icon className={`${compact ? "mb-1 h-4 w-4" : "mb-1.5 h-5 w-5"} ${selected ? "text-[#33492A]" : "text-[#5B6055]"}`} />
            )}
            <span className="max-w-full break-words">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
