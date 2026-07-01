import { useEffect, useState } from "react";
import { Link, useParams, useLocation } from "react-router-dom";
import { getFpo, getFpoFarmers, getFpoFarms, getFpoSummary, getMyFpo } from "@/lib/api/fpo";

export default function FpoDashboard() {
  const { fpoId } = useParams();
  const location = useLocation();
  const isMe = location.pathname === "/fpo/me";
  const [data, setData] = useState({ fpo: null, summary: null, farmers: [], farms: [], loading: true, error: "" });

  useEffect(() => {
    let active = true;
    const loadBase = isMe ? getMyFpo() : getFpo(fpoId);
    loadBase.then(async (fpo) => {
      const [summary, farmers, farms] = await Promise.all([
        getFpoSummary(fpo.fpo_id).catch(() => null),
        getFpoFarmers(fpo.fpo_id).catch(() => []),
        getFpoFarms(fpo.fpo_id).catch(() => []),
      ]);
      if (!active) return;
      setData({ fpo, summary, farmers, farms, loading: false, error: "" });
    }).catch((err) => {
      if (!active) return;
      setData((prev) => ({ ...prev, loading: false, error: err.message || "Failed to load FPO dashboard" }));
    });
    return () => { active = false; };
  }, [fpoId, isMe]);

  if (data.loading) return <PageState label="Loading FPO workspace..." />;
  if (data.error) return <PageState label={data.error} />;
  if (!data.fpo) return <PageState label="FPO record not found." />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{isMe ? "My FPO" : "FPO Workspace"}</div>
        <h1 className="text-3xl font-black">{data.fpo.fpo_name}</h1>
        <p className="text-sm text-muted-foreground">{data.fpo.block_name || "Block pending"}, {data.fpo.district_name}, {data.fpo.state_name}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card label="Farmers" value={data.summary?.farmer_count ?? data.farmers.length} />
        <Card label="Farms" value={data.summary?.farm_count ?? data.farms.length} />
        <Card label="Area acres" value={Number(data.summary?.total_area_acres || 0).toFixed(2)} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 text-lg font-bold">Farmers under this FPO</div>
          <div className="space-y-3">
            {data.farmers.length ? data.farmers.map((farmer) => (
              <Link key={farmer.farmer_id} to={`/farmers/${farmer.farmer_id}`} className="block rounded-2xl border p-4 hover:bg-muted/30">
                <div className="font-semibold">{farmer.full_name}</div>
                <div className="text-sm text-muted-foreground">{farmer.village_name || "Village pending"} • {farmer.phone_number || "Phone pending"}</div>
              </Link>
            )) : <div className="text-sm text-muted-foreground">No farmer rows available.</div>}
          </div>
        </section>
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 text-lg font-bold">Farms under this FPO</div>
          <div className="space-y-3">
            {data.farms.length ? data.farms.map((farm) => (
              <Link key={farm.farm_id} to={`/land/${farm.farm_id}`} className="block rounded-2xl border p-4 hover:bg-muted/30">
                <div className="font-semibold">{farm.farm_name || farm.survey_number || "Unnamed farm"}</div>
                <div className="text-sm text-muted-foreground">{farm.village_name || "Village pending"} • {Number(farm.area_acres || 0).toFixed(2)} acres</div>
              </Link>
            )) : <div className="text-sm text-muted-foreground">No farm rows available.</div>}
          </div>
        </section>
      </div>
    </div>
  );
}

function Card({ label, value }) {
  return <div className="rounded-3xl border bg-card p-4"><div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{label}</div><div className="mt-2 text-2xl font-black">{value}</div></div>;
}
function PageState({ label }) {
  return <div className="grid min-h-[40vh] place-items-center p-6 text-sm text-muted-foreground">{label}</div>;
}
