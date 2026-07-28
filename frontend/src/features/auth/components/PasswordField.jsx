import {
  forwardRef,
  useId,
  useState,
} from "react";

import PasswordStrength from "@/features/auth/components/PasswordStrength";

const PasswordField = forwardRef(function PasswordField(
  {
    label,
    error,
    showStrength = false,
    value,
    onChange,
    name,
    id: providedId,
    autoComplete = "new-password",
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const inputId =
    providedId ||
    `${name || "password"}-${generatedId}`;

  const errorId = `${inputId}-error`;

  const [visible, setVisible] = useState(false);

  return (
    <div className="block">
      <label
        htmlFor={inputId}
        className="text-sm font-semibold text-slate-700"
      >
        {label}
      </label>

      <div className="relative mt-1">
        <input
          {...props}
          id={inputId}
          ref={ref}
          name={name}
          type={visible ? "text" : "password"}
          autoComplete={autoComplete}
          value={value}
          onChange={onChange}
          aria-invalid={Boolean(error)}
          aria-describedby={
            error ? errorId : undefined
          }
          className={`w-full rounded-xl border px-3 py-2.5 pr-16 outline-none transition ${
            error
              ? "border-rose-400 focus:border-rose-600"
              : "border-slate-300 focus:border-emerald-600"
          }`}
        />

        <button
          type="button"
          onClick={() =>
            setVisible((current) => !current)
          }
          aria-label={
            visible
              ? `Hide ${label.toLowerCase()}`
              : `Show ${label.toLowerCase()}`
          }
          className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>

      {error ? (
        <p
          id={errorId}
          className="mt-1 text-xs text-rose-600"
        >
          {error}
        </p>
      ) : null}

      {showStrength ? (
        <PasswordStrength value={value} />
      ) : null}
    </div>
  );
});

export default PasswordField;