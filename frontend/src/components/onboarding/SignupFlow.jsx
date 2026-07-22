import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  Building2,
  Check,
  CheckCircle2,
  ChevronRight,
  Leaf,
  Lock,
  Mail,
  Phone,
  Shield,
  User,
  UserCircle2,
  Wheat,
} from "lucide-react";
import { startSignup, verifySignupOtp, completeSignup } from "@/lib/api/auth";

const INITIAL = {
  full_name: "",
  phone_number: "",
  email: "",
  password: "",
  confirm_password: "",
  role: "farmer",
  fpo_id: "",
  invite_code: "",
  consent_terms: false,
};

const STEPS = [
  { id: "account", label: "Account" },
  { id: "verify", label: "OTP" },
  { id: "details", label: "Details" },
  { id: "done", label: "Done" },
];

export default function SignupFlow() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(INITIAL);
  const [otp, setOtp] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState({});

  const progress = useMemo(() => [22, 50, 80, 100][step] || 10, [step]);
  const isFarmer = form.role === "farmer";

  const canStart =
    form.full_name.trim() &&
    form.phone_number.replace(/\D/g, "").length === 10 &&
    form.password.length >= 8 &&
    form.password === form.confirm_password &&
    form.consent_terms;

  useEffect(() => {
    if (step !== 3) return;
    const timer = window.setTimeout(() => navigate("/login", { replace: true, state: { signupSuccess: "Details registered with MaatiTrace." } }), 4000);
    return () => window.clearTimeout(timer);
  }, [navigate, step]);

  const setValue = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const begin = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await startSignup(form);
      setSessionId(response.signup_session_id);
      setDevOtp(response.dev_otp || "");
      setStep(1);
    } catch (err) {
      setError(err.message || "Unable to start signup.");
    } finally {
      setLoading(false);
    }
  };

  const verify = async () => {
    setLoading(true);
    setError("");
    try {
      await verifySignupOtp({ signup_session_id: sessionId, otp });
      setStep(2);
    } catch (err) {
      setError(err.message || "OTP verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const complete = async () => {
    setLoading(true);
    setError("");
    try {
      await completeSignup({ signup_session_id: sessionId, role: form.role, profile });
      setStep(3);
    } catch (err) {
      setError(err.message || "Unable to complete signup.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[linear-gradient(180deg,#eff5ef_0%,#f6f1e7_52%,#edf3ee_100%)] px-4 py-6 text-slate-900">
      <div className="absolute inset-0 opacity-60 [background-image:radial-gradient(rgba(7,61,46,0.06)_1px,transparent_1px)] [background-size:28px_28px]" />
      <div className="absolute -left-24 top-16 h-72 w-72 rounded-full bg-emerald-200/50 blur-3xl" />
      <div className="absolute -right-24 bottom-0 h-96 w-96 rounded-full bg-amber-100/70 blur-3xl" />

      <div className="relative mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/82 shadow-[0_30px_100px_rgba(15,23,42,0.12)] backdrop-blur-xl">
            <div className="border-b border-slate-200/70 bg-slate-50/80 px-6 py-5 md:px-8">
              <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.35em] text-emerald-700">MaatiTrace Onboarding</p>
                  <h1 className="mt-2 text-2xl font-black tracking-tight text-slate-950 md:text-3xl">
                    Launch your account in a clean, guided flow
                  </h1>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                    Keep signup light. Complete only the essentials now, then finish profile detail later in Settings.
                  </p>
                </div>
                <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3">
                  <Leaf className="h-5 w-5 text-emerald-700" />
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">Privacy first</p>
                    <p className="text-xs text-slate-600">Masked identifiers where possible</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-5 md:px-8">
              <StepHeader step={step} progress={progress} />

              <AnimatePresence mode="wait">
                <motion.div
                  key={step}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -16 }}
                  transition={{ duration: 0.28 }}
                >
                  {step === 0 && (
                    <div className="space-y-4">
                      <Field
                        label="Full name"
                        icon={UserCircle2}
                        value={form.full_name}
                        onChange={(e) => setValue("full_name", e.target.value)}
                        placeholder="Ramesh Sahoo"
                      />
                      <Field
                        label="Phone number"
                        icon={Phone}
                        value={form.phone_number}
                        onChange={(e) => setValue("phone_number", e.target.value)}
                        placeholder="10 digit mobile number"
                      />
                      <Field
                        label="Email"
                        icon={Mail}
                        value={form.email}
                        onChange={(e) => setValue("email", e.target.value)}
                        placeholder="you@example.com"
                        optional
                      />
                      <div className="grid gap-4 md:grid-cols-2">
                        <Field
                          label="Password"
                          icon={Lock}
                          type="password"
                          value={form.password}
                          onChange={(e) => setValue("password", e.target.value)}
                          placeholder="Minimum 8 characters"
                        />
                        <Field
                          label="Confirm password"
                          icon={Lock}
                          type="password"
                          value={form.confirm_password}
                          onChange={(e) => setValue("confirm_password", e.target.value)}
                          placeholder="Repeat password"
                        />
                      </div>
                      <RolePicker role={form.role} onChange={(role) => setValue("role", role)} />
                      <Field
                        label="FPO ID / invite code"
                        icon={Building2}
                        value={form.fpo_id}
                        onChange={(e) => setValue("fpo_id", e.target.value)}
                        placeholder="Optional for linked farmers"
                        optional
                      />
                      <ConsentStrip
                        checked={form.consent_terms}
                        onChange={(checked) => setValue("consent_terms", checked)}
                      />
                      {error && <InlineError message={error} />}
                      <ActionButton disabled={!canStart || loading} onClick={begin} loading={loading} label="Continue" />
                    </div>
                  )}

                  {step === 1 && (
                    <div className="space-y-5">
                      <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50/90 p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">OTP Verification</p>
                            <h2 className="mt-1 text-xl font-black text-slate-950">Confirm your phone or email</h2>
                            <p className="mt-2 max-w-xl text-sm text-slate-600">
                              Enter the 6-digit code sent to your device. If you are testing locally, the code is shown below.
                            </p>
                          </div>
                          <Shield className="h-10 w-10 text-emerald-700" />
                        </div>
                        {devOtp ? (
                          <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                            Local development OTP: <span className="font-bold">{devOtp}</span>
                          </div>
                        ) : null}
                      </div>

                      <OtpInput value={otp} onChange={setOtp} />

                      {error && <InlineError message={error} />}

                      <div className="grid gap-3 sm:grid-cols-2">
                        <button
                          type="button"
                          onClick={() => setStep(0)}
                          className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                        >
                          <ArrowLeft className="h-4 w-4" />
                          Change details
                        </button>
                        <ActionButton disabled={loading || otp.length !== 6} onClick={verify} loading={loading} label="Verify OTP" />
                      </div>
                    </div>
                  )}

                  {step === 2 && (
                    <div className="space-y-5">
                      <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50/90 p-5">
                        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">Role details</p>
                        <h2 className="mt-1 text-xl font-black text-slate-950">
                          {isFarmer ? "Farmer profile essentials" : "FPO organisation essentials"}
                        </h2>
                        <p className="mt-2 max-w-2xl text-sm text-slate-600">
                          Keep this step practical. You can add deeper profile details later in Settings.
                        </p>
                      </div>

                      <RoleDetailsFields role={form.role} profile={profile} setProfile={setProfile} />

                      {error && <InlineError message={error} />}

                      <div className="grid gap-3 sm:grid-cols-2">
                        <button
                          type="button"
                          onClick={() => setStep(1)}
                          className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                        >
                          <ArrowLeft className="h-4 w-4" />
                          Back
                        </button>
                        <ActionButton disabled={loading} onClick={complete} loading={loading} label="Complete signup" />
                      </div>
                    </div>
                  )}

                  {step === 3 && (
                    <div className="space-y-6 py-5 text-center">
                      <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 20 }}
                        className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-emerald-200 bg-emerald-50"
                      >
                        <CheckCircle2 className="h-10 w-10 text-emerald-700" />
                      </motion.div>
                      <div>
                        <h2 className="text-2xl font-black tracking-tight text-slate-950">
                          Details registered with MaatiTrace
                        </h2>
                        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">
                          {isFarmer
                            ? "You can now log in and register your first land."
                            : "You can now log in and add farmers or register land."}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => navigate("/login", { replace: true })}
                        className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-slate-950 px-6 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
                      >
                        Go to Login
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          <aside className="rounded-[2rem] border border-white/70 bg-white/72 p-6 shadow-[0_30px_100px_rgba(15,23,42,0.1)] backdrop-blur-xl">
            <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-emerald-700">Design language</p>
              <h3 className="mt-2 text-xl font-black text-slate-950">Strong, practical, premium</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                The onboarding keeps the same step structure, but the visual language is more grounded and less decorative.
              </p>
            </div>

            <div className="mt-5 space-y-3">
              <FeatureRow title="Minimal data capture" text="Only essential identity details now." />
              <FeatureRow title="Role-based expansion" text="Farmer and FPO details split cleanly." />
              <FeatureRow title="Settings later" text="Deeper profile inputs stay editable afterward." />
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

function StepHeader({ step, progress }) {
  return (
    <div className="mb-5">
      <div className="mb-4 flex items-center gap-3">
        {STEPS.map((item, index) => (
          <React.Fragment key={item.id}>
            <div className="flex flex-col items-center gap-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border text-[10px] font-black transition-colors ${
                  index <= step ? "border-emerald-700 bg-emerald-700 text-white" : "border-slate-200 bg-white text-slate-400"
                }`}
              >
                {index < step ? <Check className="h-3.5 w-3.5" /> : index + 1}
              </div>
              <span className={`text-[10px] font-semibold uppercase tracking-[0.18em] ${index === step ? "text-slate-900" : "text-slate-400"}`}>
                {item.label}
              </span>
            </div>
            {index < STEPS.length - 1 && <div className={`mb-5 h-px flex-1 ${index < step ? "bg-emerald-700" : "bg-slate-200"}`} />}
          </React.Fragment>
        ))}
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <motion.div className="h-full rounded-full bg-emerald-700" animate={{ width: `${progress}%` }} transition={{ duration: 0.45 }} />
      </div>
    </div>
  );
}

function Field({ label, icon: Icon, optional = false, ...props }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">
        {label} {optional ? <span className="font-medium normal-case tracking-normal text-slate-400">(optional)</span> : null}
      </span>
      <div className="relative">
        <Icon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          {...props}
          className="w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-3 pl-10 text-sm text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-emerald-600"
        />
      </div>
    </label>
  );
}

function RolePicker({ role, onChange }) {
  return (
    <div>
      <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Registering as</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {[
          { value: "farmer", title: "Farmer", subtitle: "Individual or household profile", icon: Wheat },
          { value: "fpo", title: "FPO", subtitle: "Organisation profile", icon: Building2 },
        ].map((item) => {
          const active = role === item.value;
          const Icon = item.icon;
          return (
            <button
              key={item.value}
              type="button"
              onClick={() => onChange(item.value)}
              className={`rounded-[1.25rem] border px-4 py-4 text-left transition-colors ${
                active ? "border-emerald-700 bg-emerald-50" : "border-slate-200 bg-white hover:bg-slate-50"
              }`}
            >
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 bg-white">
                <Icon className={`h-5 w-5 ${active ? "text-emerald-700" : "text-slate-500"}`} />
              </div>
              <div className="text-sm font-bold text-slate-950">{item.title}</div>
              <div className="mt-1 text-xs leading-5 text-slate-500">{item.subtitle}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ConsentStrip({ checked, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`flex w-full items-start gap-3 rounded-[1.25rem] border p-4 text-left transition-colors ${
        checked ? "border-emerald-700 bg-emerald-50" : "border-slate-200 bg-white hover:bg-slate-50"
      }`}
    >
      <span
        className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-md border ${
          checked ? "border-emerald-700 bg-emerald-700" : "border-slate-300 bg-white"
        }`}
      >
        {checked ? <Check className="h-3.5 w-3.5 text-white" /> : null}
      </span>
      <span className="text-sm text-slate-700">
        I agree to data processing and app terms.
        <span className="mt-1 block text-xs leading-5 text-slate-500">
          MaatiTrace stores verification status and masked identifiers where possible.
        </span>
      </span>
    </button>
  );
}

function OtpInput({ value, onChange }) {
  return (
    <div>
      <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">6-digit OTP</p>
      <div className="grid grid-cols-6 gap-2">
        {Array.from({ length: 6 }).map((_, index) => (
          <input
            key={index}
            inputMode="numeric"
            autoComplete="one-time-code"
            value={value[index] || ""}
            onChange={(e) => {
              const digit = e.target.value.replace(/\D/g, "").slice(-1);
              const next = value.split("");
              next[index] = digit;
              onChange(next.join("").slice(0, 6));
              if (digit && e.target.nextElementSibling) {
                e.target.nextElementSibling.focus();
              }
            }}
            className="h-14 rounded-2xl border border-slate-200 bg-white text-center text-xl font-black tracking-[0.2em] text-slate-950 outline-none transition-colors focus:border-emerald-700"
          />
        ))}
      </div>
    </div>
  );
}

function RoleDetailsFields({ role, profile, setProfile }) {
  const fields =
    role === "farmer"
      ? [
          ["gender", "Gender", "text"],
          ["date_of_birth", "Date of birth", "date"],
          ["preferred_language", "Preferred language", "text"],
          ["aadhaar_last4", "Aadhaar last 4 digits", "text"],
          ["state_name", "State", "text"],
          ["district_name", "District", "text"],
          ["block_name", "Block", "text"],
          ["village_name", "Village", "text"],
          ["farmer_type", "Farmer type", "text"],
          ["primary_crop", "Primary crop", "text"],
          ["irrigation_status", "Irrigation status", "text"],
        ]
      : [
          ["fpo_name", "FPO name", "text"],
          ["registration_number", "Registration number", "text"],
          ["registration_type", "Registration type", "text"],
          ["date_of_registration", "Date of registration", "date"],
          ["promoted_by", "Promoted by", "text"],
          ["promoting_institution_name", "Promoting institution", "text"],
          ["state_name", "State", "text"],
          ["district_name", "District", "text"],
          ["block_name", "Block", "text"],
          ["contact_person_name", "Contact person", "text"],
          ["contact_person_designation", "Designation", "text"],
          ["contact_phone", "Phone", "text"],
          ["contact_email", "Email", "email"],
          ["main_commodities", "Main commodities", "text"],
        ];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {fields.map(([key, label, type]) => (
        <label key={key} className="block">
          <span className="mb-1.5 block text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">{label}</span>
          <input
            type={type}
            value={profile[key] || ""}
            onChange={(e) => setProfile((prev) => ({ ...prev, [key]: e.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-emerald-700"
          />
        </label>
      ))}
    </div>
  );
}

function FeatureRow({ title, text }) {
  return (
    <div className="rounded-[1.25rem] border border-slate-200 bg-white p-4">
      <div className="text-sm font-bold text-slate-950">{title}</div>
      <div className="mt-1 text-sm leading-6 text-slate-600">{text}</div>
    </div>
  );
}

function ActionButton({ disabled, loading, onClick, label }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-slate-950 px-5 text-sm font-semibold text-white transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {loading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : null}
      {label}
      {!loading ? <ChevronRight className="h-4 w-4" /> : null}
    </button>
  );
}

function InlineError({ message }) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {message}
    </div>
  );
}
