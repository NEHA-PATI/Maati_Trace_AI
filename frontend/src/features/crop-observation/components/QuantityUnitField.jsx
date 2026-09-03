import { Minus, Plus } from "lucide-react";

const COMMON_UNITS = ["kg", "g", "L", "ml", "bags"];

export default function QuantityUnitField({ value, onChange }) {
  const amount = typeof value?.value === "number" ? value.value : "";
  const unit = value?.unit || COMMON_UNITS[0];

  function setAmount(next) {
    onChange({ value: next, unit });
  }

  function step(delta) {
    const current = typeof amount === "number" ? amount : 0;
    setAmount(Math.max(0, current + delta));
  }

  return (
    <div>
      <div className="flex items-center justify-between rounded-2xl bg-[#F1F5EA] p-2">
        <button
          type="button"
          onClick={() => step(-1)}
          className="grid h-12 w-12 place-items-center rounded-xl bg-white text-[#4B6B3A] shadow-sm active:scale-[0.98]"
          aria-label="Decrease"
        >
          <Minus className="h-5 w-5" />
        </button>
        <div className="flex min-w-0 flex-1 items-baseline justify-center gap-2 px-3">
          <input
            type="number"
            inputMode="decimal"
            min="0"
            value={amount}
            onChange={(event) => {
              const parsed = event.target.value === "" ? "" : Number(event.target.value);
              setAmount(parsed === "" ? "" : parsed);
            }}
            className="h-12 w-24 bg-transparent text-center text-2xl font-black text-[#1D2117] outline-none"
          />
          <span className="text-sm font-bold text-[#5B6055]">{unit}</span>
        </div>
        <button
          type="button"
          onClick={() => step(1)}
          className="grid h-12 w-12 place-items-center rounded-xl bg-white text-[#4B6B3A] shadow-sm active:scale-[0.98]"
          aria-label="Increase"
        >
          <Plus className="h-5 w-5" />
        </button>
      </div>

      <div className="mt-2 grid grid-cols-5 gap-2">
        {COMMON_UNITS.map((nextUnit) => (
          <button
            key={nextUnit}
            type="button"
            onClick={() => onChange({ value: amount === "" ? 0 : amount, unit: nextUnit })}
            className={`min-h-11 rounded-xl border text-sm font-bold transition active:scale-[0.98] ${
              unit === nextUnit
                ? "border-[#4B6B3A] bg-[#E1F1D6] text-[#33492A]"
                : "border-[#E9E7DC] bg-white text-[#5B6055]"
            }`}
          >
            {nextUnit}
          </button>
        ))}
      </div>
    </div>
  );
}
