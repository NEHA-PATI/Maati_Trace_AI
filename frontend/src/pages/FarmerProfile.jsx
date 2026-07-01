import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getFarmer, getFarmerFarms, getFarmerSummary, getMyFarmerProfile } from "@/lib/api/farmer";
import { getStoredUser } from "@/lib/auth/session";

export default function FarmerProfile() {
  const { farmerId } = useParams();
  const location = useLocation();
  const isMe = location.pathname === "/farmer/me";
  const storedUser = getStoredUser();
  const [data, setData] = useState({ farmer: null, summary: null, farms: [], loading: true, error: "" });

  useEffect(() => {
    if (isMe && storedUser?.role && storedUser.role !== "farmer") {
      setData({
        farmer: null,
        summary: null,
        farms: [],
        loading: false,
        error: "Current user is not a farmer user.",
      });
      return undefined;
    }

    let active = true;
    const loadFarmer = isMe ? getMyFarmerProfile() : getFarmer(farmerId);
    loadFarmer.then(async (farmer) => {
      const [summary, farms] = await Promise.all([
        getFarmerSummary(farmer.farmer_id).catch(() => null),
        getFarmerFarms(farmer.farmer_id).catch(() => []),
      ]);
      if (!active) return;
      setData({ farmer, summary, farms, loading: false, error: "" });
    }).catch((err) => {
      if (!active) return;
      if (isMe && (err?.message || "").toLowerCase().includes("not linked")) {
        setData({
          farmer: {
            farmer_id: "pending-profile",
            full_name: storedUser?.full_name || "New Farmer",
            phone_number: storedUser?.phone_number || null,
            fpo_id: null,
            village_name: null,
            block_name: null,
            district_name: "Unassigned",
          },
          summary: { farm_count: 0, total_area_acres: 0 },
          farms: [],
          loading: false,
          error: "",
        });
        return;
      }
      setData((prev) => ({ ...prev, loading: false, error: err.message || "Failed to load farmer profile" }));
    });
    return () => { active = false; };
  }, [farmerId, isMe, storedUser?.full_name, storedUser?.phone_number, storedUser?.role]);

  if (data.loading) return <PageState label="Loading farmer profile..." />;
  if (data.error) return <PageState label={data.error} />;
  if (!data.farmer) return <PageState label="Farmer profile not found." />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{isMe ? "My Farmer Profile" : "Farmer Profile"}</div>
        <h1 className="text-3xl font-black">{data.farmer.full_name}</h1>
        <p className="text-sm text-muted-foreground">{data.farmer.village_name || "Village pending"} • {data.farmer.block_name || "Block pending"} • {data.farmer.district_name}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card label="Phone" value={data.farmer.phone_number || "pending"} />
        <Card label="FPO" value={data.farmer.fpo_id || "independent"} />
        <Card label="Farm count" value={data.summary?.farm_count ?? data.farms.length} />
        <Card label="Area acres" value={Number(data.summary?.total_area_acres || 0).toFixed(2)} />
      </div>
      <section className="rounded-3xl border bg-card p-5">
        <div className="mb-4 text-lg font-bold">Registered farms</div>
        <div className="grid gap-4 md:grid-cols-2">
          {data.farms.length ? data.farms.map((farm) => (
            <Link key={farm.farm_id} to={`/land/${farm.farm_id}`} className="rounded-2xl border p-4 hover:bg-muted/30">
              <div className="font-semibold">{farm.farm_name || farm.survey_number || "Unnamed farm"}</div>
              <div className="text-sm text-muted-foreground">{farm.village_name || "Village pending"} • {Number(farm.area_acres || 0).toFixed(2)} acres • H3 {farm.h3_cell_count || 0}</div>
            </Link>
          )) : <div className="text-sm text-muted-foreground">No farms registered for this farmer yet. <Link to="/farm-register" className="font-semibold text-primary">Register your first farm</Link>.</div>}
        </div>
      </section>
    </div>
  );
}

function Card({ label, value }) {
  return <div className="rounded-3xl border bg-card p-4"><div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{label}</div><div className="mt-2 text-xl font-black break-all">{value}</div></div>;
}
function PageState({ label }) {
  return <div className="grid min-h-[40vh] place-items-center p-6 text-sm text-muted-foreground">{label}</div>;
}
