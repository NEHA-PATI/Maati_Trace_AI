export default function ChoiceField({ field, value, onChange }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {(field.options || []).map((option) => (
        <button
          key={option.option_code}
          type="button"
          onClick={() => onChange(option.option_code)}
          className={`min-h-[52px] rounded-xl border-2 px-3 py-2 text-base font-semibold transition-colors ${
            value === option.option_code
              ? "border-emerald-600 bg-emerald-50 text-emerald-900"
              : "border-slate-300 bg-white text-slate-900 hover:border-slate-400"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
