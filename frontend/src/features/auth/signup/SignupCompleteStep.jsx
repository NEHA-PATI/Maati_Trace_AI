import { Link } from "react-router-dom";
import { AUTH_ROUTES } from "@/features/auth/authRoutes";

export default function SignupCompleteStep({ user }) {
  return (
    <div className="py-4 text-center">
      <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-100 text-3xl text-emerald-700">✓</div>
      <h2 className="mt-5 text-2xl font-black text-slate-950">Account created. You are signed in.</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Welcome, {user?.full_name || "farmer"}. Complete your profile now or register your first land.
      </p>
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Link to={AUTH_ROUTES.completeProfile} className="rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-800 hover:bg-slate-50">Complete Profile</Link>
        <Link to={AUTH_ROUTES.registerLand} className="rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800">Register Land</Link>
      </div>
    </div>
  );
}
