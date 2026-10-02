import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { UserRound } from "lucide-react";
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
  const authorizedFarms = farms.data || [];
  const authorizedArea = authorizedFarms.reduce(
    (total, farm) => total + Number(farm.area_acres || 0),
    0,
  );

  const value = (field, fallback = "Not provided") => item[field] || fallback;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <Link to="/fpo/farmers" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Back to farmers
        </Link>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-emerald-50 text-emerald-700" aria-label="Farmer profile image placeholder">
                {item.profile_image_url ? <img src={item.profile_image_url} alt="" className="h-16 w-16 rounded-2xl object-cover" /> : <UserRound className="h-8 w-8" aria-hidden="true" />}
              </div>
              <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Farmer monitoring dashboard</p>
              <h1 className="mt-1 text-2xl font-semibold text-slate-900">{value("full_name", item.farmer_name || "Farmer")}</h1>
              <p className="mt-2 text-sm text-slate-600">{item.district_name || "District unavailable"} · {item.village_name || "Village unavailable"}</p>
              </div>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
              {item.relationship_status || "ACTIVE"}
            </span>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Authorized farms</p><p className="mt-1 text-2xl font-black text-slate-950">{authorizedFarms.length || item.farm_count || 0}</p></div>
            <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Authorized area</p><p className="mt-1 text-2xl font-black text-slate-950">{authorizedArea.toFixed(2)} <span className="text-sm font-bold">acres</span></p></div>
            <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Relationship</p><p className="mt-1 text-sm font-black uppercase text-emerald-700">{item.relationship_status || "ACTIVE"}</p></div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Consent-authorized profile</p>
              <h2 className="mt-1 text-xl font-semibold text-slate-900">Farmer details</h2>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Read only</span>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[
              ["Email", value("email")],
              ["Phone number", value("phone_number")],
              ["Gender", value("gender")],
              ["Aadhaar last 4 digits", value("aadhaar_last4")],
              ["KYC status", value("kyc_status")],
              ["State", value("state_name")],
              ["District", value("district_name")],
              ["Block", value("block_name")],
              ["Village", value("village_name")],
              ["Total landholding", item.total_landholding_acres != null ? `${item.total_landholding_acres} acres` : "Not provided"],
              ["Cultivated area", item.cultivated_area_acres != null ? `${item.cultivated_area_acres} acres` : "Not provided"],
              ["Primary crop", value("primary_crop")],
            ].map(([label, fieldValue]) => (
              <div key={label} className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-400">{label}</p>
                <p className="mt-1 break-words text-sm font-semibold text-slate-900">{fieldValue}</p>
              </div>
            ))}
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
