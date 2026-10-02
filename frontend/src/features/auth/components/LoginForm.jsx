import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import PasswordField from "@/features/auth/components/PasswordField";
import { loginSchema } from "@/features/auth/authValidation";
import { useTranslation, validationMessage } from "@/features/i18n";

export default function LoginForm({ onSubmit, loading = false, error = "" }) {
  const { t } = useTranslation();
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { identifier: "", password: "" },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <label className="block">
        <span className="text-sm font-semibold text-slate-700">{t("auth.emailOrPhone")}</span>
        <input
          {...register("identifier")}
          autoComplete="username"
          className={`mt-1 w-full rounded-xl border px-3 py-2.5 outline-none ${errors.identifier ? "border-rose-400" : "border-slate-300 focus:border-emerald-600"}`}
        />
        {errors.identifier ? <p className="mt-1 text-xs text-rose-600">{validationMessage(errors.identifier.message, t)}</p> : null}
      </label>
      <PasswordField
        label={t("auth.password")}
        autoComplete="current-password"
        error={errors.password?.message ? validationMessage(errors.password.message, t) : undefined}
        {...register("password")}
      />
      {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? t("auth.signingIn") : t("auth.signIn")}
      </button>
    </form>
  );
}
