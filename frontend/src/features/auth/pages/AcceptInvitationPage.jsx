import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useSearchParams } from "react-router-dom";

import { authApi } from "@/features/auth/api/authApi";
import { getDefaultRouteForRole } from "@/features/auth/authRoutes";
import AuthLayout from "@/features/auth/components/AuthLayout";
import PasswordField from "@/features/auth/components/PasswordField";
import { useAuth } from "@/features/auth/context/useAuth";
import { invitationAcceptSchema } from "@/features/auth/authValidation";

export default function AcceptInvitationPage() {
  const [searchParams] = useSearchParams();
  const [token] = useState(() => searchParams.get("token") || "");
  const navigate = useNavigate();
  const { adoptAuthResponse } = useAuth();
  const [validation, setValidation] = useState({ loading: true, valid: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    resolver: zodResolver(invitationAcceptSchema),
    defaultValues: { full_name: "", phone_number: "", password: "", confirm_password: "" },
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

  useEffect(() => {
    let active = true;
    if (!token) {
      setValidation({ loading: false, valid: false });
      return undefined;
    }
    authApi.validateInvitation(token)
      .then((response) => { if (active) setValidation({ loading: false, ...response }); })
      .catch((requestError) => {
        if (active) {
          setError(requestError.message || "This invitation is invalid.");
          setValidation({ loading: false, valid: false });
        }
      });
    return () => { active = false; };
  }, [token]);

  async function submit(values) {
    setLoading(true);
    setError("");
    try {
      const response = await authApi.acceptInvitation({
        token,
        full_name: values.full_name,
        phone_number: values.phone_number,
        password: values.password,
      });
      const user = adoptAuthResponse(response);
      navigate(getDefaultRouteForRole(user.role), { replace: true });
    } catch (requestError) {
      setError(requestError.message || "The invitation could not be accepted.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Accept MaatiTrace invitation" subtitle={validation.masked_email ? `Invitation for ${validation.masked_email}` : "Set up the invited account securely."}>
      {validation.loading ? <p className="text-sm text-slate-600">Validating invitation…</p> : null}
      {!validation.loading && !validation.valid ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error || "This invitation is expired, revoked, or already used."}</div> : null}
      {validation.valid ? (
        <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">Account role: <strong>{validation.role}</strong></div>
          <div>
  <label
    htmlFor="invitation-full-name"
    className="text-sm font-semibold text-slate-700"
  >
    Full name
  </label>

  <input
    id="invitation-full-name"
    {...register("full_name")}
    autoComplete="name"
    className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5"
  />

  {errors.full_name ? (
    <p className="mt-1 text-xs text-rose-600">
      {errors.full_name.message}
    </p>
  ) : null}
</div>
<div>
  <label
    htmlFor="invitation-phone-number"
    className="text-sm font-semibold text-slate-700"
  >
    Indian mobile number
  </label>

  <input
    id="invitation-phone-number"
    {...register("phone_number")}
    inputMode="tel"
    autoComplete="tel"
    className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5"
  />

  {errors.phone_number ? (
    <p className="mt-1 text-xs text-rose-600">
      {errors.phone_number.message}
    </p>
  ) : null}
</div>
          <PasswordField
  id="invitation-password"
  label="Create password"
  showStrength
  value={password}
  error={errors.password?.message}
  {...register("password")}
/>

<PasswordField
  id="invitation-confirm-password"
  label="Confirm password"
  error={errors.confirm_password?.message}
  {...register("confirm_password")}
/>
          {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
          <button disabled={loading} className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white disabled:opacity-60">{loading ? "Creating account…" : "Accept invitation"}</button>
        </form>
      ) : null}
    </AuthLayout>
  );
}
