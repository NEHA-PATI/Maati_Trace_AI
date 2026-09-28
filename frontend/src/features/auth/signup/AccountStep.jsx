import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import PasswordField from "@/features/auth/components/PasswordField";
import { signupAccountSchema } from "@/features/auth/authValidation";

const EMPTY = {
  account_type: "farmer",
  full_name: "",
  email: "",
  phone_number: "",
  password: "",
  confirm_password: "",
  consent_terms: false,
  authorised_fpo_representative: false,
  organisation_name: "",
  registration_type: "producer_company",
  registration_number: "",
  state_code: "",
  district_code: "",
};

export default function AccountStep({
  defaultValues = EMPTY,
  onContinue,
  loading,
  error,
}) {
  const {
    register,
    setValue,
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
  const accountType = watch("account_type");

  return (
    <form
      onSubmit={handleSubmit(onContinue)}
      className="space-y-4"
      noValidate
    >
      <fieldset>
        <legend className="text-sm font-semibold text-slate-700">Registering as</legend>
        <div className="mt-2 grid gap-3 sm:grid-cols-2">
          {[{ value: "farmer", title: "Farmer", description: "Manage your own farms and crop records." }, { value: "fpo", title: "Farmer Producer Organisation", description: "Set up an organisation workspace for your members." }].map((option) => (
            <label key={option.value} className={`cursor-pointer rounded-xl border p-3 ${accountType === option.value ? "border-emerald-600 bg-emerald-50" : "border-slate-200"}`}>
              <input {...register("account_type", { onChange: (event) => { if (event.target.value === "farmer") { setValue("authorised_fpo_representative", false); } } })} type="radio" value={option.value} className="sr-only" />
              <span className="block font-semibold text-slate-800">{option.title}</span>
              <span className="mt-1 block text-xs leading-5 text-slate-500">{option.description}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {accountType === "fpo" ? (
        <section className="space-y-3 rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4">
          <div>
            <h3 className="font-semibold text-slate-800">FPO basics</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">We only need these details to start your workspace. Complete the full profile after verification.</p>
          </div>
          <div>
            <label htmlFor="signup-organisation-name" className="text-sm font-semibold text-slate-700">Organisation name</label>
            <input id="signup-organisation-name" {...register("organisation_name")} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5" />
            {errors.organisation_name ? <p className="mt-1 text-xs text-rose-600">{errors.organisation_name.message}</p> : null}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="signup-registration-type" className="text-sm font-semibold text-slate-700">Registration type</label>
              <select id="signup-registration-type" {...register("registration_type")} className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5">
                <option value="producer_company">Producer company</option><option value="cooperative_society">Cooperative society</option><option value="other">Other</option>
              </select>
            </div>
            <div>
              <label htmlFor="signup-registration-number" className="text-sm font-semibold text-slate-700">Registration number</label>
              <input id="signup-registration-number" {...register("registration_number")} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5" />
              {errors.registration_number ? <p className="mt-1 text-xs text-rose-600">{errors.registration_number.message}</p> : null}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div><label htmlFor="signup-state-code" className="text-sm font-semibold text-slate-700">State code</label><input id="signup-state-code" type="number" {...register("state_code")} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5" />{errors.state_code ? <p className="mt-1 text-xs text-rose-600">{errors.state_code.message}</p> : null}</div>
            <div><label htmlFor="signup-district-code" className="text-sm font-semibold text-slate-700">District code</label><input id="signup-district-code" type="number" {...register("district_code")} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5" />{errors.district_code ? <p className="mt-1 text-xs text-rose-600">{errors.district_code.message}</p> : null}</div>
          </div>
          <label className="flex items-start gap-3 rounded-xl border border-emerald-100 bg-white p-3"><input {...register("authorised_fpo_representative")} type="checkbox" className="mt-1 h-4 w-4 accent-emerald-700" /><span className="text-sm leading-6 text-slate-600">I am authorised to register this FPO and will provide accurate information.</span></label>
          {errors.authorised_fpo_representative ? <p className="text-xs text-rose-600">{errors.authorised_fpo_representative.message}</p> : null}
        </section>
      ) : null}

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
