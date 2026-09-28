import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getFpoPortalBootstrap } from "../api/fpoPortalApi";

const copy = {
  PROFILE_INCOMPLETE: ["Complete your FPO profile", "Add the organization details and operating information before submitting verification."],
  READY_TO_SUBMIT: ["Ready for verification", "Review your profile and submit the verification request."],
  SUBMITTED: ["Verification submitted", "Your request is waiting for administrator review."],
  UNDER_REVIEW: ["Verification under review", "The verification team is reviewing the submitted organization snapshot."],
  CHANGES_REQUIRED: ["Changes required", "Update the requested profile fields and submit verification again."],
  REJECTED: ["Verification rejected", "Review the administrator decision and contact support if you need help."],
  SUSPENDED: ["FPO access suspended", "Portfolio access is unavailable while the organization is suspended."],
};

export default function FpoLifecycleBoundary({ children }) {
  const location = useLocation();
  const query = useQuery({ queryKey: ["fpo-portal-bootstrap"], queryFn: getFpoPortalBootstrap, refetchInterval: 30000 });
  if (query.isLoading) return <div className="grid min-h-[50vh] place-items-center text-sm text-slate-500">Preparing your secure FPO workspace…</div>;
  if (query.isError) return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">Unable to load FPO workspace status. Please retry shortly.</div>;
  const status = query.data?.verification?.status || "PROFILE_INCOMPLETE";
  const provisioning = query.data?.organization?.provisioning_status || query.data?.status;
  const allowed = status === "APPROVED" && query.data?.organization?.lifecycle_status === "ACTIVE" && provisioning === "READY";
  const profileRoute = "/fpo/profile";
  if (allowed || location.pathname === profileRoute || location.pathname === "/fpo/verification") return children;
  const [title, message] = copy[status] || (provisioning !== "READY" ? ["Preparing your organization", "Your FPO organization is being provisioned. This page will update automatically."] : ["FPO verification required", "Complete verification before opening portfolio data."]);
  return <section className="mx-auto max-w-2xl rounded-3xl border border-emerald-100 bg-white p-8 shadow-sm"><div className="mb-5 inline-flex rounded-full bg-amber-50 px-3 py-1 text-xs font-black uppercase tracking-wide text-amber-800">{status.replaceAll("_", " ")}</div><h1 className="text-2xl font-black text-slate-950">{title}</h1><p className="mt-3 text-sm leading-6 text-slate-600">{message}</p><div className="mt-6 flex flex-wrap gap-3"><Link to={profileRoute} className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-bold text-white">Open profile</Link><Link to="/fpo/verification" className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-700">View verification</Link></div></section>;
}
