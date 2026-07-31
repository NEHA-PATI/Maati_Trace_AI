import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { authApi } from "@/features/auth/api/authApi";
import AuthLayout from "@/features/auth/components/AuthLayout";
import { forgotPasswordSchema } from "@/features/auth/authValidation";

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  async function submit(values) {
    setLoading(true);
    setError("");
    try {
      const response = await authApi.forgotPassword(values.email);
      setMessage(response.message);
    } catch (requestError) {
      setError(requestError.message || "The request could not be completed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We return the same response whether or not an account exists."
      footer={<Link to="/login" className="font-semibold text-emerald-700 hover:underline">Back to sign in</Link>}
    >
      {message ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900">{message}</div>
      ) : (
        <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Email address</span>
            <input {...register("email")} type="email" autoComplete="email" className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none focus:border-emerald-600" />
            {errors.email ? <p className="mt-1 text-xs text-rose-600">{errors.email.message}</p> : null}
          </label>
          {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
          <button disabled={loading} className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white disabled:opacity-60">
            {loading ? "Submitting…" : "Send reset link"}
          </button>
        </form>
      )}
    </AuthLayout>
  );
}
