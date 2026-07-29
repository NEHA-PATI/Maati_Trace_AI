import { Link } from "react-router-dom";

export default function AuthLayout({ title, subtitle, children, footer, backTo = "/" }) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(16,185,129,0.12),transparent_35%),linear-gradient(180deg,#f8faf7_0%,#eef7ef_100%)] px-4 py-10">
      <div className="mx-auto w-full max-w-md">
        <Link to={backTo} className="mb-6 inline-flex text-sm font-semibold text-emerald-800 hover:underline">
          ← Back
        </Link>
        <section className="rounded-3xl border border-white/70 bg-white/90 p-6 shadow-xl backdrop-blur md:p-8">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-emerald-700">MaatiTrace</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">{title}</h1>
          {subtitle ? <p className="mt-2 text-sm leading-6 text-slate-600">{subtitle}</p> : null}
          <div className="mt-6">{children}</div>
        </section>
        {footer ? <div className="mt-5 text-center text-sm text-slate-600">{footer}</div> : null}
      </div>
    </main>
  );
}
