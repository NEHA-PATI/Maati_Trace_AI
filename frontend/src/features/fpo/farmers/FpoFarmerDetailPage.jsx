import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getFpoFarmer, getFpoFarmerFarms } from "../api/fpoFarmerApi";

export default function FpoFarmerDetailPage() {
  const { farmerId } = useParams();
  const farmer = useQuery({
    queryKey: ["fpo-farmer", farmerId],
    queryFn: () => getFpoFarmer(farmerId),
    enabled: Boolean(farmerId),
  });
  const farms = useQuery({
    queryKey: ["fpo-farmer-farms", farmerId],
    queryFn: () => getFpoFarmerFarms(farmerId),
    enabled: Boolean(farmerId),
  });

  if (farmer.isLoading) {
    return <p className="p-6 text-sm text-slate-600">Loading farmer profile…</p>;
  }
  if (farmer.isError) {
    return <p className="p-6 text-sm text-red-700">Unable to load this farmer profile.</p>;
  }

  const item = farmer.data || {};
  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <Link to="/fpo/farmers" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Back to farmers
        </Link>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Farmer monitoring dashboard</p>
              <h1 className="mt-1 text-2xl font-semibold text-slate-900">{item.farmer_name || "Farmer"}</h1>
              <p className="mt-2 text-sm text-slate-600">{item.district_name || "District unavailable"} · {item.village_name || "Village unavailable"}</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
              {item.relationship_status || "ACTIVE"}
            </span>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Registered farms</p><p className="mt-1 text-2xl font-black text-slate-950">{farms.data?.length || item.farm_count || 0}</p></div>
            <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Area monitored</p><p className="mt-1 text-2xl font-black text-slate-950">{item.area_acres ?? 0} <span className="text-sm font-bold">acres</span></p></div>
            <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Relationship</p><p className="mt-1 text-sm font-black uppercase text-emerald-700">{item.relationship_status || "ACTIVE"}</p></div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Farms</h2>
              <p className="mt-1 text-sm text-slate-600">Open the same consent-authorized land intelligence surface used to monitor this farmer’s farm.</p>
            </div>
            <span className="text-sm text-slate-500">{farms.data?.length || 0} registered</span>
          </div>

          {farms.isLoading && <p className="mt-6 text-sm text-slate-600">Loading farms…</p>}
          {farms.isError && <p className="mt-6 text-sm text-red-700">Unable to load this farmer’s farms.</p>}
          {!farms.isLoading && !farms.isError && farms.data?.length ? (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {farms.data.map((farm) => (
                <article key={farm.farm_id} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-900">{farm.farm_name || "Unnamed farm"}</h3>
                      <p className="mt-1 text-sm text-slate-600">{farm.village_name || "Village unavailable"} · {farm.area_acres ?? "—"} acres</p>
                    </div>
                    <span className="text-xs font-medium text-slate-500">{farm.crop_name || farm.crop_code || "Crop unavailable"}</span>
                  </div>
                  <Link
                    to={`/fpo/farmers/${encodeURIComponent(farmerId)}/farms/${encodeURIComponent(farm.farm_id)}/intelligence`}
                    className="mt-4 inline-flex rounded-lg bg-emerald-700 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-800"
                  >
                    Open intelligence
                  </Link>
                </article>
              ))}
            </div>
          ) : null}
          {!farms.isLoading && !farms.isError && !farms.data?.length && (
            <p className="mt-6 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">No farms are available for this active relationship.</p>
          )}
        </section>
      </div>
    </div>
  );
}
