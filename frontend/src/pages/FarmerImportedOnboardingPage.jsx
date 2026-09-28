import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  MapPin,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { Link } from "react-router-dom";
import { getFarmerImportedOnboarding } from "@/lib/api/fpo";

const labels = {
  AWAITING_FARMER_ACCOUNT: "Complete your account",
  AWAITING_FARM_CONFIRMATION: "Confirm farm details",
  AWAITING_CONSENT: "Review data sharing",
  READY_FOR_RELATIONSHIP: "Ready to connect",
  CREATED: "Completed",
  FAILED: "Needs attention",
};

function nextAction(record) {
  const status = record.status;
  if (status === "AWAITING_FARMER_ACCOUNT")
    return { label: "Complete profile", to: "/farmer/me" };
  if (status === "AWAITING_FARM_CONFIRMATION")
    return {
      label: "Review farm details",
      to: `/farm-register?staged_record_id=${record.staged_record_id}`,
    };
  if (status === "AWAITING_CONSENT")
    return { label: "Open FPO connections", to: "/farmer/fpo" };
  return { label: "Open FPO connections", to: "/farmer/fpo" };
}

function Detail({ label, value }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-[10px] font-black uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-sm font-bold text-slate-800">
        {value || "Not provided"}
      </p>
    </div>
  );
}

export default function FarmerImportedOnboardingPage() {
  const query = useQuery({
    queryKey: ["farmer-imported-onboarding"],
    queryFn: getFarmerImportedOnboarding,
  });
  const records = query.data || [];

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 pb-24 md:p-8">
      <header className="rounded-3xl bg-slate-950 p-6 text-white md:p-8">
        <Link
          to="/farmer/fpo"
          className="text-xs font-bold text-emerald-300 hover:underline"
        >
          ← Back to FPO connections
        </Link>
        <div className="mt-6 flex items-start gap-4">
          <div className="rounded-2xl bg-emerald-500/20 p-3">
            <UserRound className="h-6 w-6 text-emerald-300" />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-300">
              Farmer onboarding
            </p>
            <h1 className="mt-2 text-3xl font-black">
              Review shared farm information
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              An FPO may have submitted information to help you get started. You
              remain in control: confirm your farm, review the requested
              purpose, and give consent before any FPO can access it.
            </p>
          </div>
        </div>
      </header>

      {query.isLoading && (
        <section className="rounded-3xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
          Loading onboarding records…
        </section>
      )}
      {query.isError && (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">
          We could not load your imported onboarding records. Please try again
          later.
        </section>
      )}
      {!query.isLoading && !query.isError && !records.length && (
        <section className="rounded-3xl border border-slate-200 bg-white p-8 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600" />
          <h2 className="mt-4 text-xl font-black text-slate-950">
            You have no pending imported records
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-slate-500">
            You can discover approved FPOs and connect a specific farm whenever
            you are ready.
          </p>
          <Link
            to="/farmer/fpo"
            className="mt-5 inline-flex items-center rounded-xl bg-emerald-700 px-4 py-3 text-sm font-black text-white"
          >
            Explore FPO connections <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </section>
      )}

      <div className="space-y-4">
        {records.map((record) => {
          const payload = record.payload || {};
          const action = nextAction(record);
          return (
            <article
              key={record.staged_record_id}
              className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"
            >
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 p-5 md:p-6">
                <div className="flex items-start gap-3">
                  <div className="rounded-xl bg-emerald-50 p-2.5">
                    <FileText className="h-5 w-5 text-emerald-700" />
                  </div>
                  <div>
                    <p className="text-xs font-black uppercase tracking-wide text-emerald-700">
                      Imported {String(record.record_type).toLowerCase()}{" "}
                      information
                    </p>
                    <h2 className="mt-1 text-xl font-black text-slate-950">
                      {payload.farm_name ||
                        payload.farmer_name ||
                        "Onboarding record"}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                      {record.status_reason}
                    </p>
                  </div>
                </div>
                <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-black uppercase tracking-wide text-amber-800">
                  {labels[record.status] ||
                    String(record.status).replaceAll("_", " ")}
                </span>
              </div>
              <div className="grid gap-6 p-5 md:grid-cols-[1fr_0.8fr] md:p-6">
                <div className="grid gap-3 sm:grid-cols-2">
                  <Detail label="Farmer" value={payload.farmer_name} />
                  <Detail label="Farm" value={payload.farm_name} />
                  <Detail label="Crop" value={payload.crop_name} />
                  <Detail
                    label="Area"
                    value={
                      payload.area_acres ? `${payload.area_acres} acres` : null
                    }
                  />
                  <Detail label="Village" value={payload.village_name} />
                  <Detail label="District" value={payload.district_name} />
                </div>
                <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-4">
                  <div className="flex items-start gap-3">
                    <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
                    <div>
                      <p className="text-sm font-black text-emerald-950">
                        Your control comes first
                      </p>
                      <p className="mt-1 text-xs leading-5 text-emerald-900">
                        This record does not give an FPO access to your farm.
                        Access begins only after you confirm the farm and accept
                        a consent request.
                      </p>
                    </div>
                  </div>
                  <Link
                    to={action.to}
                    className="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-emerald-700 px-4 py-3 text-sm font-black text-white hover:bg-emerald-800"
                  >
                    {action.label}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </div>
              </div>
              <div className="flex items-center gap-2 border-t border-slate-100 px-5 py-3 text-xs text-slate-500 md:px-6">
                <MapPin className="h-4 w-4" />
                Imported details are suggestions until you confirm them.
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
