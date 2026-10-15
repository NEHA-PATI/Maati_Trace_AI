import { useQuery } from "@tanstack/react-query";
import { Outlet } from "react-router-dom";
import { getFpoPortalBootstrap } from "@/features/fpo/api/fpoPortalApi";
import FpoSidebar from "./FpoSidebar";
import FpoTopbar from "./FpoTopbar";
import FpoMobileNavigation from "./FpoMobileNavigation";
import { FpoPortalContext } from "./FpoPortalContext";

export default function FpoAppShell() {
  const query = useQuery({ queryKey: ["fpo-portal-bootstrap"], queryFn: getFpoPortalBootstrap, refetchInterval: 30000 });
  const bootstrap = query.data;
  return <FpoPortalContext.Provider value={{ bootstrap, entitlements: bootstrap?.entitlements || {} }}><div className="min-h-screen bg-[#fafaf8] text-slate-900"><div className="min-h-screen lg:pl-64"><FpoSidebar /><div className="min-w-0"><FpoTopbar /><main className="mx-auto max-w-[1600px] px-4 py-6 pb-24 md:px-6 md:py-6 md:pb-8">{query.isLoading ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Preparing your FPO workspace…</div> : query.isError ? <div className="rounded-2xl border border-rose-200 bg-rose-50 p-8 text-sm text-rose-700">Unable to load the FPO workspace.</div> : <Outlet />}</main></div></div><FpoMobileNavigation /></div></FpoPortalContext.Provider>;
}
