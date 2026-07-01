import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import FarmMapView from "@/components/ui-custom/FarmMapView";
import { getFarm } from "@/lib/api/farm";
import {
  getFarmGridCells,
  getFarmSummary,
  getFarmTrends,
  getLatestGridValues,
  getLatestSentinel2,
  getSentinel2History,
} from "@/lib/api/analytics";
import { materializeFarmAnalysis, materializeFarmGrid, materializeFarmTrends } from "@/lib/api/hotStream";
import { canViewTechnicalH3Layer } from "@/lib/rbac/permissions";
import { getStoredUser } from "@/lib/auth/session";
import { Button } from "@/components/ui/button";

const METRICS = [
  ["avg_ndvi", "Vegetation health"],
  ["avg_ndmi", "Moisture balance"],
  ["avg_ndwi", "Water presence"],
  ["avg_bsi", "Bare soil exposure"],
  ["avg_evi", "Crop vigor"],
  ["avg_savi", "Canopy stability"],
  ["avg_msi", "Moisture stress"],
  ["avg_nbr", "Burn or damage risk"],
  ["avg_ndre", "Leaf chlorophyll"],
];

export default function LandIntelligence() {
  const { farmId } = useParams();
  const [state, setState] = useState({ loading: true, error: "", farm: null, summary: null, latest: null, history: null, trends: null, gridCells: null, gridValues: null, running: false });
  const user = getStoredUser();

  const load = async () => {
    setState((prev) => ({ ...prev, loading: true, error: "" }));
    try {
      const [farm, summary, latest, history, trends, gridCells, gridValues] = await Promise.all([
        getFarm(farmId),
        getFarmSummary(farmId).catch(() => null),
        getLatestSentinel2(farmId).catch(() => null),
        getSentinel2History(farmId, 10).catch(() => null),
        getFarmTrends(farmId).catch(() => null),
        getFarmGridCells(farmId).catch(() => null),
        getLatestGridValues(farmId).catch(() => null),
      ]);
      setState({ loading: false, error: "", farm, summary, latest, history, trends, gridCells, gridValues, running: false });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error: error.message || "Failed to load land intelligence" }));
    }
  };

  useEffect(() => { load(); }, [farmId]);

  const humanMetrics = useMemo(() => METRICS.map(([key, label]) => ({ label, value: state.latest?.[key] })), [state.latest]);

  const runLatest = async () => {
    setState((prev) => ({ ...prev, running: true }));
    try {
      await materializeFarmAnalysis(farmId, {
        start_date: "2026-01-01",
        end_date: "2026-07-01",
        max_cloud_cover: 30,
        h3_resolution: 12,
      });
      await materializeFarmTrends(farmId, {});
      await materializeFarmGrid(farmId, {});
    } catch {
      // keep UI resilient; report pending below through existing data states
    }
    await load();
  };

  if (state.loading) return <PageState label="Loading land intelligence..." />;
  if (state.error) return <PageState label={state.error} />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Land Intelligence</div>
          <h1 className="text-3xl font-black">{state.farm?.farm_name || state.farm?.survey_number || "Farm profile"}</h1>
          <p className="text-sm text-muted-foreground">{state.farm?.village_name || "Village pending"} • {state.farm?.block_name || "Block pending"} • {state.farm?.district_name}</p>
        </div>
        <Button onClick={runLatest} disabled={state.running}>{state.running ? "Running latest analysis..." : "Run latest analysis"}</Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-3xl border bg-card p-4">
          <FarmMapView />
          <div className="mt-3 text-xs text-muted-foreground">
            Visual truth is the grid layer. Boundary is highlighted in red. Free map tiles are still available in the reusable Leaflet components for follow-up replacement if you want the view fully geographic.
          </div>
        </section>
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 text-lg font-bold">Latest snapshot</div>
          <div className="grid gap-3 sm:grid-cols-2">
            {humanMetrics.map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} />
            ))}
          </div>
          <div className="mt-4 grid gap-2 text-sm">
            <div>Pixel count: {state.latest?.total_pixel_count ?? "pending"}</div>
            <div>Valid pixels: {state.latest?.total_valid_pixel_count ?? "pending"}</div>
            <div>Cloud percentage: {state.latest?.avg_cloud_percentage ?? "pending"}</div>
            <div>Vegetation signal: {state.summary?.vegetation_signal ?? "pending"}</div>
            <div>Moisture signal: {state.summary?.moisture_signal ?? "pending"}</div>
            <div>Bare soil signal: {state.summary?.bare_soil_signal ?? "pending"}</div>
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 text-lg font-bold">Trend history</div>
          <pre className="overflow-auto rounded-2xl bg-muted p-4 text-xs">{JSON.stringify(state.history?.items || state.trends?.items || [], null, 2)}</pre>
        </section>
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 text-lg font-bold">Grid values</div>
          <pre className="overflow-auto rounded-2xl bg-muted p-4 text-xs">{JSON.stringify(state.gridValues?.items || [], null, 2)}</pre>
          {canViewTechnicalH3Layer(user) ? (
            <div className="mt-4 rounded-2xl border border-dashed p-4 text-xs text-muted-foreground">
              H3 technical layer toggle is allowed for this role. H3 detail endpoint can be bound here with the same page shell.
            </div>
          ) : null}
        </section>
      </div>

      {(!state.gridCells?.items?.length || !state.gridValues?.items?.length) ? (
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          Grid materialization data is not available yet for this farm. The page stays live and keeps showing the latest satellite analytics that are already stored.
        </div>
      ) : null}
    </div>
  );
}

function MetricCard({ label, value }) {
  return <div className="rounded-2xl border p-4"><div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{label}</div><div className="mt-2 text-xl font-black">{value ?? "pending"}</div></div>;
}
function PageState({ label }) {
  return <div className="grid min-h-[40vh] place-items-center p-6 text-sm text-muted-foreground">{label}</div>;
}
