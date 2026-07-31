import { useMemo, useRef } from "react";

function normaliseOtp(value) {
  return String(value || "").replace(/\D/g, "").slice(0, 6);
}

export default function OtpInput({ value, onChange, disabled = false, autoFocus = true }) {
  const refs = useRef([]);
  const digits = useMemo(() => Array.from({ length: 6 }, (_, index) => value[index] || ""), [value]);

  function update(index, digit) {
    const next = digits.slice();
    next[index] = digit;
    onChange(next.join(""));
  }

  function handleChange(index, event) {
    const incoming = normaliseOtp(event.target.value);
    if (incoming.length > 1) {
      const next = digits.slice();
      incoming.split("").forEach((digit, offset) => {
        if (index + offset < 6) next[index + offset] = digit;
      });
      onChange(next.join(""));
      refs.current[Math.min(index + incoming.length, 5)]?.focus();
      return;
    }
    update(index, incoming);
    if (incoming && index < 5) refs.current[index + 1]?.focus();
  }

  function handleKeyDown(index, event) {
    if (event.key === "Backspace") {
  event.preventDefault();

  if (digits[index]) {
    update(index, "");

    if (index > 0) {
      refs.current[index - 1]?.focus();
    }

    return;
  }

  if (index > 0) {
    update(index - 1, "");
    refs.current[index - 1]?.focus();
  }

  return;
} else if (event.key === "ArrowLeft" && index > 0) {
      event.preventDefault();
      refs.current[index - 1]?.focus();
    } else if (event.key === "ArrowRight" && index < 5) {
      event.preventDefault();
      refs.current[index + 1]?.focus();
    } else if (event.key === "Home") {
      event.preventDefault();
      refs.current[0]?.focus();
    } else if (event.key === "End") {
      event.preventDefault();
      refs.current[5]?.focus();
    }
  }

  function handlePaste(event) {
    event.preventDefault();
    const pasted = normaliseOtp(event.clipboardData.getData("text"));
    if (!pasted) return;
    onChange(pasted);
    refs.current[Math.min(pasted.length, 6) - 1]?.focus();
  }

  return (
    <fieldset disabled={disabled}>
      <legend className="mb-2 text-sm font-semibold text-slate-700">Six-digit email verification code</legend>
      <div className="grid grid-cols-6 gap-2" onPaste={handlePaste}>
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(node) => { refs.current[index] = node; }}
            value={digit}
            onChange={(event) => handleChange(index, event)}
            onKeyDown={(event) => handleKeyDown(index, event)}
            inputMode="numeric"
            pattern="[0-9]*"
            autoComplete={index === 0 ? "one-time-code" : "off"}
            autoFocus={autoFocus && index === 0}
            maxLength={1}
            aria-label={`OTP digit ${index + 1} of 6`}
            className="h-14 min-w-0 rounded-xl border border-slate-300 text-center text-xl font-black outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100"
          />
        ))}
      </div>
    </fieldset>
  );
}
