import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router-dom";

import { authApi } from "@/features/auth/api/authApi";
import AuthLayout from "@/features/auth/components/AuthLayout";
import PasswordField from "@/features/auth/components/PasswordField";
import { resetPasswordSchema } from "@/features/auth/authValidation";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const [token] = useState(() => searchParams.get("token") || "");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: "", confirm_password: "" },
  });
  const password = watch("password");

  useEffect(() => {
    const meta = document.createElement("meta");
    meta.name = "referrer";
    meta.content = "no-referrer";
    document.head.appendChild(meta);
    if (window.location.search) {
      window.history.replaceState(window.history.state, document.title, window.location.pathname);
    }
    return () => meta.remove();
  }, []);

  async function submit(values) {
    setLoading(true);
    setError("");
    try {
      const response = await authApi.resetPassword(token, values.password);
      setMessage(response.message);
    } catch (requestError) {
      setError(requestError.message || "The reset link could not be used.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return <AuthLayout title="Invalid reset link" subtitle="This URL does not contain a password-reset token."><Link to="/forgot-password" className="font-semibold text-emerald-700">Request another reset link</Link></AuthLayout>;
  }

  return (
    <AuthLayout title="Choose a new password" subtitle="Successful reset revokes your existing authenticated sessions.">
      {message ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{message}</div>
          <Link to="/login" className="block rounded-xl bg-emerald-700 px-4 py-3 text-center font-semibold text-white">Sign in</Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
          <PasswordField
  id="reset-password"
  label="New password"
  showStrength
  value={password}
  error={errors.password?.message}
  {...register("password")}
/>

<PasswordField
  id="reset-confirm-password"
  label="Confirm new password"
  error={errors.confirm_password?.message}
  {...register("confirm_password")}
/>
          {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
          <button disabled={loading} className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white disabled:opacity-60">{loading ? "Resetting…" : "Reset password"}</button>
        </form>
      )}
    </AuthLayout>
  );
}
