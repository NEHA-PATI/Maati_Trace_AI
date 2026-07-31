import { useEffect, useState } from "react";
import OtpInput from "@/features/auth/components/OtpInput";

function formatTime(total) {
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export default function VerifyOtpStep({
  maskedEmail,
  otp,
  onOtpChange,
  onVerify,
  onResend,
  onBack,
  onRestart,
  loading,
  error,
  expiresAt,
  resendAvailableAt,
  resendsRemaining,
}) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const expirySeconds = Math.max(0, Math.ceil((expiresAt - now) / 1000));
  const resendSeconds = Math.max(0, Math.ceil((resendAvailableAt - now) / 1000));
  const expired = expirySeconds === 0;
  const canResend = resendSeconds === 0 && resendsRemaining > 0 && !loading;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
        <h2 className="font-bold text-slate-950">Check your email</h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">Enter the code sent to <strong>{maskedEmail}</strong>.</p>
        <p className={`mt-2 text-xs font-semibold ${expired ? "text-rose-600" : "text-emerald-800"}`}>
          {expired ? "This code has expired. Request a new code." : `Code expires in ${formatTime(expirySeconds)}.`}
        </p>
      </div>

      <OtpInput value={otp} onChange={onOtpChange} disabled={loading} />

      {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}

      <button
        type="button"
        onClick={onVerify}
        disabled={loading || otp.length !== 6 || expired}
        className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Verifying…" : "Verify and create account"}
      </button>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <button type="button" onClick={onBack} disabled={loading} className="font-semibold text-slate-600 hover:text-slate-950">← Change account details</button>
        <button type="button" onClick={onResend} disabled={!canResend} className="font-semibold text-emerald-700 disabled:text-slate-400">
          {resendSeconds > 0 ? `Resend in ${resendSeconds}s` : resendsRemaining > 0 ? `Resend code (${resendsRemaining} left)` : "Resend limit reached"}
        </button>
      </div>
      {expired && resendsRemaining === 0 ? (
        <button type="button" onClick={onRestart} disabled={loading} className="w-full text-sm font-semibold text-rose-700 hover:underline">
          Start signup again
        </button>
      ) : null}
    </div>
  );
}
