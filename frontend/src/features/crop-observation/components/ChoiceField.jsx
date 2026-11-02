import { colorForOption, iconForOption } from "./fieldIcons";
import { systemMediaUrl } from "@/features/crop-observation/api/cropObservationApi";

function gridClass(count) {
  if (count >= 4) return "grid-cols-2 min-[360px]:grid-cols-4 gap-2";
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
            className={`flex min-w-0 flex-col items-center justify-center rounded-[14px] border-2 text-center font-bold leading-[1.15] transition active:scale-[0.98] ${
              compact ? "h-[82px] px-1 py-2 text-[12px]" : "min-h-[68px] px-2.5 py-2 text-sm"
            } ${
              selected
                ? "border-[#4B6B3A] bg-[#E1F1D6] text-[#33492A] shadow-[0_3px_12px_rgba(75,107,58,0.14)]"
                : "border-[#E9E7DC] bg-white text-[#1D2117] hover:border-[#C9D8BD]"
            }`}
          >
            {option.image_url ? (
              <img src={systemMediaUrl(option.image_url)} alt="" className="mb-2 h-16 w-full rounded-lg object-cover" loading="lazy" />
            ) : (
              <span className={`mb-1 grid shrink-0 place-items-center rounded-full ${compact ? "h-7 w-7" : "h-8 w-8"} ${selected ? "bg-[#CFE8C1]" : "bg-[#F4F7F0]"}`}>
                <Icon className={`${compact ? "h-4 w-4" : "h-5 w-5"} ${selected ? "text-[#33492A]" : colorForOption(option.option_code)}`} />
              </span>
            )}
            <span className="line-clamp-2 max-w-full overflow-hidden">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
