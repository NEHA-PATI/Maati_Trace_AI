import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import PasswordField from "@/features/auth/components/PasswordField";
import { signupAccountSchema } from "@/features/auth/authValidation";

const EMPTY = {
  full_name: "",
  email: "",
  phone_number: "",
  password: "",
  confirm_password: "",
  consent_terms: false,
};

export default function AccountStep({
  defaultValues = EMPTY,
  onContinue,
  loading,
  error,
}) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(signupAccountSchema),
    defaultValues: {
      ...EMPTY,
      ...defaultValues,
    },
  });

  const password = watch("password");

  return (
    <form
      onSubmit={handleSubmit(onContinue)}
      className="space-y-4"
      noValidate
    >
      <div>
        <label
          htmlFor="signup-full-name"
          className="text-sm font-semibold text-slate-700"
        >
          Full name
        </label>

        <input
          id="signup-full-name"
          {...register("full_name")}
          autoComplete="name"
          aria-invalid={Boolean(errors.full_name)}
          className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none focus:border-emerald-600"
        />

        {errors.full_name ? (
          <p className="mt-1 text-xs text-rose-600">
            {errors.full_name.message}
          </p>
        ) : null}
      </div>

      <div>
        <label
          htmlFor="signup-email"
          className="text-sm font-semibold text-slate-700"
        >
          Email address
        </label>

        <input
          id="signup-email"
          {...register("email")}
          type="email"
          autoComplete="email"
          aria-invalid={Boolean(errors.email)}
          className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none focus:border-emerald-600"
        />

        {errors.email ? (
          <p className="mt-1 text-xs text-rose-600">
            {errors.email.message}
          </p>
        ) : null}
      </div>

      <div>
        <label
          htmlFor="signup-phone-number"
          className="text-sm font-semibold text-slate-700"
        >
          Indian mobile number
        </label>

        <input
          id="signup-phone-number"
          {...register("phone_number")}
          inputMode="tel"
          autoComplete="tel"
          placeholder="9876543210"
          aria-invalid={Boolean(errors.phone_number)}
          className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none focus:border-emerald-600"
        />

        <p className="mt-1 text-xs text-slate-500">
          Stored securely in E.164 format, for example
          +919876543210.
        </p>

        {errors.phone_number ? (
          <p className="mt-1 text-xs text-rose-600">
            {errors.phone_number.message}
          </p>
        ) : null}
      </div>

      <PasswordField
        id="signup-password"
        label="Create password"
        showStrength
        value={password}
        error={errors.password?.message}
        {...register("password")}
      />

      <PasswordField
        id="signup-confirm-password"
        label="Confirm password"
        error={errors.confirm_password?.message}
        {...register("confirm_password")}
      />

      <div>
        <label className="flex items-start gap-3 rounded-xl border border-slate-200 p-3">
          <input
            {...register("consent_terms")}
            type="checkbox"
            className="mt-1 h-4 w-4 accent-emerald-700"
          />

          <span className="text-sm leading-6 text-slate-600">
            I agree to the MaatiTrace terms and privacy
            notice.
          </span>
        </label>

        {errors.consent_terms ? (
          <p className="mt-1 text-xs text-rose-600">
            {errors.consent_terms.message}
          </p>
        ) : null}
      </div>

      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800 disabled:opacity-60"
      >
        {loading
          ? "Sending verification code…"
          : "Continue"}
      </button>

      <p className="text-center text-sm text-slate-600">
        Representing an FPO?{" "}
        <Link
          to="/request-fpo-access"
          className="font-semibold text-emerald-700 hover:underline"
        >
          Request access
        </Link>
      </p>
    </form>
  );
}