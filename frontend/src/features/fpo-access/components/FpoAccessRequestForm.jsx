import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { fpoAccessSchema } from "@/features/fpo-access/fpoAccessValidation";

export default function FpoAccessRequestForm({ onSubmit, loading, error }) {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(fpoAccessSchema),
    defaultValues: {
      organisation_name: "",
      registration_number: "",
      contact_person_name: "",
      contact_email: "",
      contact_phone: "",
      state_name: "Odisha",
      district_name: "",
      message: "",
    },
  });

  const field = (name, label, type = "text") => (
    <label className="block">
      <span className="text-sm font-semibold text-slate-700">{label}</span>
      <input {...register(name)} type={type} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none focus:border-emerald-600" />
      {errors[name] ? <p className="mt-1 text-xs text-rose-600">{errors[name].message}</p> : null}
    </label>
  );

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      {field("organisation_name", "FPO organisation name")}
      {field("registration_number", "Registration number (optional)")}
      {field("contact_person_name", "Contact person")}
      {field("contact_email", "Contact email", "email")}
      {field("contact_phone", "Indian mobile number", "tel")}
      <div className="grid gap-4 sm:grid-cols-2">
        {field("state_name", "State")}
        {field("district_name", "District")}
      </div>
      <label className="block">
        <span className="text-sm font-semibold text-slate-700">Message (optional)</span>
        <textarea {...register("message")} rows={5} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 outline-none focus:border-emerald-600" />
        {errors.message ? <p className="mt-1 text-xs text-rose-600">{errors.message.message}</p> : null}
      </label>
      {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
      <button disabled={loading} className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white disabled:opacity-60">{loading ? "Submitting request…" : "Request FPO access"}</button>
    </form>
  );
}
