import { Minus, Plus } from "lucide-react";

const COMMON_UNITS = ["kg", "g", "L", "ml", "bags"];

export default function QuantityUnitField({ value, onChange }) {
  const amount = typeof value?.value === "number" ? value.value : "";
  const unit = value?.unit || "";

  function setAmount(next) {
    onChange({ value: next, unit: unit || COMMON_UNITS[0] });
  }

  function step(delta) {
    const current = typeof amount === "number" ? amount : 0;
    setAmount(Math.max(0, current + delta));
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center overflow-hidden rounded-xl border-2 border-slate-200">
        <button
          type="button"
          onClick={() => step(-1)}
          className="grid h-12 w-12 place-items-center text-slate-500 hover:bg-slate-50"
          aria-label="Decrease"
        >
          <Minus className="h-4 w-4" />
        </button>
        <input
          type="number"
          inputMode="decimal"
          min="0"
          value={amount}
          onChange={(event) => {
            const parsed = event.target.value === "" ? "" : Number(event.target.value);
            setAmount(parsed === "" ? "" : parsed);
          }}
          className="h-12 w-16 border-x border-slate-200 text-center text-lg font-semibold outline-none"
        />
        <button
          type="button"
          onClick={() => step(1)}
          className="grid h-12 w-12 place-items-center text-slate-500 hover:bg-slate-50"
          aria-label="Increase"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      <select
        value={unit}
        onChange={(event) => onChange({ value: amount === "" ? 0 : amount, unit: event.target.value })}
        className="h-12 flex-1 rounded-xl border-2 border-slate-200 px-3 text-sm font-medium"
      >
        {!unit ? <option value="">Unit</option> : null}
        {COMMON_UNITS.map((u) => (
          <option key={u} value={u}>
            {u}
          </option>
        ))}
      </select>
    </div>
  );
}
