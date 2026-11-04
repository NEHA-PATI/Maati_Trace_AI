import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CircleCheck, CircleDashed, LoaderCircle, RefreshCw } from "lucide-react";
import { getFpoBootstrapStatus } from "../api/fpoPortalApi";

const pollDelays = [2000, 3000, 5000];
const steps = [
  ["Account verified", "Your sign-in is verified."],
  ["Organization identity", "We are creating the permanent FPO identity."],
  ["Profile setup", "We are linking the organization profile and owner."],
  ["Workspace ready", "Your secure FPO workspace is ready."],
];

export default function FpoProvisioningPage() {
  const [bootstrap, setBootstrap] = useState(null);
  const [error, setError] = useState("");
  const [timedOut, setTimedOut] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    let timer;
    let attempts = 0;
    let serverDelay = 0;
    const expiresAt = Date.now() + 5 * 60 * 1000;

    async function poll() {
      try {
        const result = await getFpoBootstrapStatus();
        if (!active) return;
        setBootstrap(result);
        serverDelay = Number(result.next_poll_after_seconds || 0) * 1000;
        setError("");
        if (result.status === "READY" || result.status === "FAILED") return;
      } catch {
        if (!active) return;
        setError("We could not refresh the setup status. Your account is safe; try again shortly.");
      }

      if (!active) return;
      if (Date.now() >= expiresAt) {
        setTimedOut(true);
        return;
      }
      const delay = pollDelays[Math.min(attempts, pollDelays.length - 1)];
      attempts += 1;
      timer = window.setTimeout(poll, Math.max(delay, serverDelay));
    }

    setBootstrap(null);
    setError("");
    setTimedOut(false);
    poll();

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [refreshKey]);

  const status = bootstrap?.status || "PENDING";
  const ready = status === "READY";
  const failed = status === "FAILED";
  const organization = bootstrap?.organization || {};
  const organizationName = organization.display_name || bootstrap?.organization_name;
  const currentStep = ready ? 4 : status === "PROFILE_PENDING" ? 3 : status === "PROCESSING" ? 2 : 1;

  return (
    <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-9">
        <p className="text-sm font-bold uppercase tracking-wide text-emerald-700">FPO-01 · Account setup</p>
        <h1 className="mt-2 text-2xl font-black text-slate-950 sm:text-3xl">
          {ready ? "Your FPO workspace is ready" : failed ? "We need help finishing setup" : "Creating your MaatiTrace FPO workspace"}
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          {organizationName ? `Organization: ${organizationName}` : "Your verified account is being connected to its organization profile."}
        </p>

        <ol className="mt-8 space-y-4">
          {steps.map(([title, description], index) => {
            const stepNumber = index + 1;
            const complete = ready || stepNumber < currentStep;
            const active = !ready && !failed && stepNumber === currentStep;
            const Icon = complete ? CircleCheck : active ? LoaderCircle : CircleDashed;
            return (
              <li key={title} className="flex items-start gap-3">
                <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${complete ? "text-emerald-700" : active ? "animate-spin text-emerald-700" : "text-slate-300"}`} aria-hidden="true" />
                <div>
                  <p className={`text-sm font-bold ${complete || active ? "text-slate-900" : "text-slate-500"}`}>{title}</p>
                  <p className="mt-1 text-sm text-slate-600">{description}</p>
                </div>
              </li>
            );
          })}
        </ol>

        {organization.public_fpo_id ? (
          <div className="mt-7 rounded-2xl bg-emerald-50 p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-emerald-800">Your permanent FPO ID</p>
            <p className="mt-1 font-mono text-lg font-bold text-emerald-950">{organization.public_fpo_id}</p>
          </div>
        ) : null}

        {error ? <p role="alert" className="mt-6 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">{error}</p> : null}
        {timedOut ? (
          <div role="status" className="mt-6 rounded-xl bg-amber-50 p-4 text-sm text-amber-900">
            Setup is taking longer than usual. You can check again; you do not need to register a second time.
          </div>
        ) : null}
        {failed ? (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4">
            <p className="text-sm font-bold text-rose-900">{bootstrap?.error?.message || "Your workspace could not be completed."}</p>
            <p className="mt-2 text-sm text-rose-800">Contact your MaatiTrace administrator and share this reference ID.</p>
            <p className="mt-2 break-all font-mono text-xs text-rose-900">{bootstrap?.correlation_id || "Not available"}</p>
          </div>
        ) : null}

        <div className="mt-8 flex flex-wrap gap-3">
          {ready ? (
            <Link to="/fpo/profile" className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-bold text-white">Continue to organization profile</Link>
          ) : !failed && !timedOut ? (
            <p className="flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />Checking automatically…</p>
          ) : (
            <button type="button" onClick={() => setRefreshKey((key) => key + 1)} className="inline-flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold text-slate-800">
              <RefreshCw className="h-4 w-4" aria-hidden="true" /> Check again
            </button>
          )}
        </div>
      </section>
    </main>
  );
}
