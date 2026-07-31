import { passwordScore } from "@/features/auth/authValidation";

const LABELS = ["Very weak", "Weak", "Fair", "Good", "Strong"];

export default function PasswordStrength({ value }) {
  const score = passwordScore(value);
  return (
    <div className="mt-2" aria-live="polite">
      <div className="grid grid-cols-4 gap-1" aria-hidden="true">
        {[1, 2, 3, 4].map((item) => (
          <span key={item} className={`h-1.5 rounded-full ${item <= score ? "bg-emerald-600" : "bg-slate-200"}`} />
        ))}
      </div>
      <p className="mt-1 text-xs text-slate-500">Strength: {LABELS[score]}</p>
    </div>
  );
}
