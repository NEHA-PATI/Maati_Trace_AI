export default function ChoiceField({ field, value, onChange }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {(field.options || []).map((option) => (
        <button
          key={option.option_code}
          type="button"
          onClick={() => onChange(option.option_code)}
          className={`min-h-[48px] rounded-xl border-2 px-3 py-2 text-sm font-medium transition-colors ${
            value === option.option_code
              ? "border-emerald-600 bg-emerald-50 text-emerald-800"
              : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
