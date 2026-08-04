import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Activity,
  CalendarDays,
  Cloud,
  FileText,
  Hexagon,
  Leaf,
  MapPin,
  Mountain,
  RefreshCw,
  ScanLine,
  Sparkles,
  Waves,
} from "lucide-react";
import { motion as Motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import StatStrip from "@/components/ui-custom/StatStrip";
import PipelineGlassLoader from "@/components/ui-custom/PipelineGlassLoader";
import LandGridMap from "@/components/ui-custom/LandGridMap";
import {
  getLandMetric,
  interpretLandMetric,
  LAND_METRICS,
  metricValueFromCell,
  metricValueFromSummary,
} from "@/features/land-intelligence/metricInterpretation";
import { getFarm } from "@/lib/api/farm";
import {
  getFarmGridCellDetails,
  getFarmGridCells,
  getFarmH3Cells,
  getFarmSummary,
  getFarmTrends,
  getLatestGridValues,
  getLatestSentinel2,
  getSentinel2History,
} from "@/lib/api/analytics";
import { fullRefreshFarm } from "@/lib/api/hotStream";
import { canViewTechnicalH3Layer } from "@/shared/rbac/permissions";
import { getStoredUser } from "@/features/auth/session";

const PARAMETERS = [
  ...LAND_METRICS,
  { key: "temperature", name: "Surface Temperature" },
  { key: "cloud", name: "Cloud Cover" },
  { key: "valid_pixels", name: "Data Quality" },
];

const PIPELINE_STEPS = [
  "Repairing farm metadata",
  "Computing H3 cells",
  "Searching latest satellite scene",
  "Computing per-H3 satellite indices",
  "Writing H3 analytics",
  "Computing trends",
  "Building 10m grid",
  "Computing H3-to-grid coverage %",
  "Computing weighted grid values",
  "Refreshing land intelligence",
];

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.items || payload?.data || payload?.grid_cells || payload?.grid_values || payload?.h3_cells || [];
}

function pretty(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "--";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toFixed(digits);
}

function formatDate(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function valueFor(cell, param) {
  const fallback = (a, b, c) => a ?? b ?? c ?? null;
  switch (param) {
    case "ndvi":
      return fallback(cell.ndvi, cell.weighted_ndvi);
    case "evi":
      return fallback(cell.evi, cell.weighted_evi);
    case "savi":
      return fallback(cell.savi, cell.weighted_savi);
    case "ndre":
      return fallback(cell.ndre, cell.weighted_ndre);
    case "ndmi":
      return fallback(cell.ndmi, cell.weighted_ndmi);
    case "ndwi":
      return fallback(cell.ndwi, cell.weighted_ndwi);
    case "msi":
      return fallback(cell.msi, cell.weighted_msi);
    case "bsi":
      return fallback(cell.bsi, cell.weighted_bsi);
    case "nbr":
      return fallback(cell.nbr, cell.weighted_nbr);
    case "temperature":
      return fallback(cell.surface_temp_c, cell.weighted_surface_temp_c);
    case "cloud":
      return fallback(cell.cloud_percentage, cell.avg_cloud_percentage);
    case "valid_pixels":
      return fallback(cell.valid_pixel_percentage);
    default:
      return null;
  }
}

function recommendationFor(cell = {}) {
  const notes = [];
  LAND_METRICS
    .map((metric) => ({
      metric,
      result: interpretLandMetric(metric.key, metricValueFromCell(cell, metric.key)),
    }))
    .filter(({ result }) => ["critical", "needs_attention"].includes(result.status))
    .slice(0, 3)
    .forEach(({ metric, result }) => notes.push(`${metric.name}: ${result.interpretation}`));
  if (Number(cell.cloud_percentage ?? cell.avg_cloud_percentage ?? 0) > 40) notes.push("Satellite data quality reduced by cloud");
  return notes.length ? notes.join(". ") : "All available indicators are stable or within monitoring range.";
}

function MetricStatusBadge({ metricKey, value, compact = false }) {
  const result = interpretLandMetric(metricKey, value);

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${result.badgeClass} ${compact ? "px-2 py-0.5 text-[9px]" : "px-2.5 py-1 text-[10px]"}`}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: result.color }} />
      {compact ? result.shortLabel : result.label}
    </span>
  );
}

function MetricInterpretationText({ metricKey, value, className = "" }) {
  const result = interpretLandMetric(metricKey, value);

  return <span className={`${result.textClass} ${className}`}>{result.interpretation}</span>;
}

function MetricReading({ metricKey, value, compact = false }) {
  const metric = getLandMetric(metricKey);
  const result = interpretLandMetric(metricKey, value);

  if (!metric) return null;

  return (
    <div className={`group rounded-2xl border transition duration-300 hover:-translate-y-0.5 hover:shadow-md ${result.surfaceClass} ${compact ? "p-3" : "p-4"}`}>
      <div className="flex items-start justify-between gap-2">
        <p className={`${compact ? "text-xs" : "text-sm"} min-w-0 font-semibold text-slate-900`}>{metric.name}</p>
        <MetricStatusBadge metricKey={metricKey} value={value} compact />
      </div>
      <div className="mt-3">
        <MetricInterpretationText metricKey={metricKey} value={value} className="font-heading text-lg font-bold leading-tight" />
        {!compact && <p className="mt-1 text-[10px] leading-4 text-slate-500">{metric.description}</p>}
      </div>
    </div>
  );
}

export default function LandIntelligence() {
  const { farmId } = useParams();
  const user = getStoredUser();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [farm, setFarm] = useState(null);
  const [summary, setSummary] = useState(null);
  const [latestSentinel, setLatestSentinel] = useState(null);
  const [, setHistory] = useState([]);
  const [, setTrends] = useState([]);
  const [gridCells, setGridCells] = useState([]);
  const [gridValues, setGridValues] = useState([]);
  const [h3Cells, setH3Cells] = useState([]);
  const [selectedParameter, setSelectedParameter] = useState("ndvi");
  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [showH3, setShowH3] = useState(false);
  const [pipelineOpen, setPipelineOpen] = useState(false);
  const [pipelineStage, setPipelineStage] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState("");
  const [pipelineFailure, setPipelineFailure] = useState("");
  const [pipelineDetails, setPipelineDetails] = useState([]);

  function updatePipelineStage(stage, status, details = []) {
    setPipelineStage(stage);
    setPipelineStatus(status);
    setPipelineDetails(details.filter(Boolean));
  }

  async function loadLandIntelligence() {
    const [farmPayload, summaryPayload, latestPayload, historyPayload, trendsPayload, gridCellsPayload, gridValuesPayload, h3Payload] = await Promise.all([
      getFarm(farmId),
      getFarmSummary(farmId).catch(() => null),
      getLatestSentinel2(farmId).catch(() => null),
      getSentinel2History(farmId, 10).catch(() => []),
      getFarmTrends(farmId).catch(() => []),
      getFarmGridCells(farmId).catch(() => []),
      getLatestGridValues(farmId).catch(() => []),
      getFarmH3Cells(farmId).catch(() => []),
    ]);

    console.log("FARM", farmPayload);
    console.log("SUMMARY", summaryPayload);
    console.log("LATEST_SENTINEL", latestPayload);
    console.log("GRID_CELLS", gridCellsPayload);
    console.log("GRID_VALUES", gridValuesPayload);
    console.log("H3_CELLS", h3Payload);

    setFarm(farmPayload);
    setSummary(summaryPayload);
    setLatestSentinel(latestPayload);
    setHistory(normalizeList(historyPayload));
    setTrends(normalizeList(trendsPayload));
    setGridCells(normalizeList(gridCellsPayload));
    setGridValues(normalizeList(gridValuesPayload));
    setH3Cells(normalizeList(h3Payload));
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loadLandIntelligence()
      .catch((err) => {
        if (!cancelled) setError(err?.message || "Unable to load land intelligence.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [farmId]);

  useEffect(() => {
    let cancelled = false;
    async function loadDetails() {
      if (!selectedCell?.grid_cell_id) {
        setSelectedDetails(null);
        return;
      }
      const details = await getFarmGridCellDetails(farmId, selectedCell.grid_cell_id).catch(() => null);
      if (!cancelled) setSelectedDetails(details);
    }
    loadDetails();
    return () => {
      cancelled = true;
    };
  }, [farmId, selectedCell?.grid_cell_id]);

  const mergedGridCells = useMemo(() => {
    const byId = new Map(gridValues.map((value) => [String(value.grid_cell_id), value]));
    return gridCells.map((cell) => ({
      ...cell,
      ...(byId.get(String(cell.grid_cell_id)) || {}),
    }));
  }, [gridCells, gridValues]);

  const displayCells = mergedGridCells.length ? mergedGridCells : gridValues;
  const displaySelected = selectedDetails?.grid_cell || selectedCell || null;
  const latestSummary = summary || {};
  const h3Enabled = showH3 && canViewTechnicalH3Layer(user);
  const latestSceneDate = latestSentinel?.scene_datetime || latestSentinel?.observation_date || latestSummary.latest_snapshot_date;
  const latestSceneId = latestSentinel?.scene_id || latestSummary.latest_scene_id;
  const hasAnalysis = Boolean(latestSummary.has_analysis || latestSummary.latest_snapshot_date || latestSentinel?.scene_id);
  const stats = [
    { label: "Farm area", value: farm?.area_acres ? pretty(farm.area_acres, 2) : "--", unit: "ac" },
    { label: "Grid cells", value: displayCells.length || "--", unit: "" },
    { label: "H3 cells", value: summary?.total_farm_h3_cells ?? farm?.h3_cell_count ?? h3Cells.length ?? "--", unit: "" },
    { label: "Latest scene", value: latestSceneDate ? formatDate(latestSceneDate) : "No scene processed yet", unit: "" },
    { label: "Cloud cover", value: latestSentinel?.cloud_percentage ?? latestSummary.avg_cloud_percentage ?? "--", unit: "%" },
    { label: "Valid pixels", value: latestSummary.valid_pixel_percentage ?? latestSentinel?.valid_pixels_pct ?? "--", unit: "%" },
  ];
  const selectedParameterInfo = PARAMETERS.find((item) => item.key === selectedParameter);
  const summaryMetricReadings = LAND_METRICS.map((metric) => ({
    metric,
    value: metricValueFromSummary(latestSummary, metric.key),
    result: interpretLandMetric(metric.key, metricValueFromSummary(latestSummary, metric.key)),
  }));
  const statusPriority = {
    critical: 5,
    needs_attention: 4,
    watch: 3,
    good: 2,
    excellent: 1,
    unavailable: 0,
  };
  const priorityReading = [...summaryMetricReadings]
    .filter(({ result }) => result.status !== "unavailable")
    .sort((a, b) => statusPriority[b.result.status] - statusPriority[a.result.status])[0];

  async function runLatestAnalysis() {
    setRefreshing(true);
    setPipelineOpen(true);
    setPipelineFailure("");
    setPipelineDetails([]);
    try {
      updatePipelineStage(0, "Repairing farm metadata", [
        farm?.farm_name ? `Farm: ${farm.farm_name}` : `Farm ID: ${farmId}`,
      ]);

      const payload = {
        start_date: "2025-12-01",
        end_date: "2026-08-03",
        max_cloud_cover: 30,
        // Resolution is selected by the orchestrator service default.
        // h3_resolution: 12,
        provider: "planetary_computer",
        collection_id: "sentinel-2-l2a",
        use_tiny_preview_bbox: true,
        tiny_bbox_size_deg: 0.0002,
      };

      const refresh = await fullRefreshFarm(farmId, payload);
      const stages = Array.isArray(refresh?.stages) ? refresh.stages : [];
      stages.forEach((stage, index) => {
        updatePipelineStage(index, stage.name || `Stage ${index + 1}`, [
          `Status: ${stage.status}`,
          ...(stage.details ? [JSON.stringify(stage.details)] : []),
          ...(stage.message ? [stage.message] : []),
        ]);
      });

      if (refresh?.status !== "succeeded") {
        setPipelineFailure(`Pipeline completed with status: ${refresh?.status}`);
        setPipelineOpen(true);
        setPipelineStatus("Pipeline partial");
      } else {
        setPipelineStatus("Analysis complete");
        setPipelineOpen(false);
      }

      try {
        await loadLandIntelligence();
      } catch (refreshErr) {
        console.warn("Land intelligence refresh warning", refreshErr);
        setError(refreshErr?.message || "Analysis completed, but the page refresh failed. Please retry.");
      }
    } catch (err) {
      const message = err?.payload?.detail?.message || err?.message || "Analysis failed.";
      setPipelineFailure(message);
      setPipelineOpen(true);
      setPipelineStage(PIPELINE_STEPS.length - 1);
      setPipelineStatus("Pipeline failed");
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <Motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen"
    >
      <PipelineGlassLoader
        open={pipelineOpen}
        title="Land analysis pipeline"
        currentStep={pipelineStage}
        status={pipelineStatus}
        details={pipelineDetails}
        failure={pipelineFailure}
        actions={
          pipelineFailure
            ? [
                {
                  label: "Retry Analysis",
                  variant: "primary",
                  onClick: () => {
                    setPipelineFailure("");
                    runLatestAnalysis();
                  },
                },
                {
                  label: "Close",
                  onClick: () => setPipelineOpen(false),
                },
              ]
            : []
        }
      />

      <div className="mx-auto max-w-[1600px] space-y-5 p-4 md:p-6 lg:p-8">
        <section
          className="relative overflow-hidden rounded-[2.25rem] border border-emerald-900/10 bg-[#f7fbe9] shadow-[0_22px_55px_rgba(31,78,48,0.16)] xl:h-[320px]"
          style={{
            backgroundImage: "url('/image.png')",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
            backgroundSize: "106% 122%",
          }}
        >
          <div className="relative flex min-h-[610px] flex-col px-6 pb-8 pt-12 sm:px-10 md:px-14 lg:px-16 xl:absolute xl:inset-0 xl:min-h-0 xl:px-14 xl:py-4">
            <div className="max-w-[790px] xl:absolute xl:left-14 xl:top-5">
              <div className="flex items-center gap-3 text-[11px] font-extrabold uppercase tracking-[0.28em] text-[#247a58] md:text-sm xl:text-xs">
                <ScanLine className="h-4 w-4 md:h-5 md:w-5 xl:h-4 xl:w-4" />
                Land Intelligence
              </div>
              <h1 className="mt-4 font-heading text-5xl font-bold tracking-[-0.04em] text-[#123f31] md:text-6xl xl:mt-1 xl:text-3xl">
                {farm?.farm_name || "Your farm"}
              </h1>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-base font-medium text-[#527b6d] md:text-lg xl:mt-1 xl:text-sm">
                <span className="inline-flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-emerald-500 md:h-6 md:w-6 xl:h-4 xl:w-4" />
                  {farm?.village_name || "Village"}, {farm?.block_name || "Block"}, {farm?.district_name || "District"}
                </span>
                {farm?.survey_number && <span className="text-sm text-[#6f9487]">Survey {farm.survey_number}</span>}
              </div>

              <div className="mt-4 flex max-w-full flex-col gap-3 sm:flex-row xl:mt-2 xl:gap-2">
                <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-[#6f9d8c]/70 bg-white/80 px-5 py-3 text-xs font-semibold text-[#194f3d] shadow-sm backdrop-blur-sm md:text-sm xl:px-4 xl:py-1.5 xl:text-xs">
                  <CalendarDays className="h-4 w-4 text-emerald-500" />
                  Scene {latestSceneDate ? formatDate(latestSceneDate) : "not processed"}
                </span>
                <span className="inline-flex min-w-0 items-center gap-2 rounded-full border border-[#6f9d8c]/70 bg-white/80 px-5 py-3 text-xs font-semibold text-[#194f3d] shadow-sm backdrop-blur-sm md:text-sm xl:max-w-xl xl:px-4 xl:py-1.5 xl:text-xs">
                  <FileText className="h-4 w-4 shrink-0 text-emerald-500" />
                  <span className="truncate">{latestSceneId || "No satellite scene yet"}</span>
                </span>
              </div>
            </div>

            <Button
              onClick={runLatestAnalysis}
              disabled={refreshing}
              className="mt-6 h-14 self-start rounded-2xl bg-[#d8fa78] px-7 text-base font-bold text-[#123f31] shadow-[0_12px_25px_rgba(47,104,50,0.2)] hover:bg-[#c9f45b] xl:absolute xl:right-14 xl:top-[88px] xl:mt-0 xl:h-11 xl:px-7 xl:text-sm"
            >
              <RefreshCw className={`mr-3 h-5 w-5 ${refreshing ? "animate-spin" : ""}`} />
              Run Latest Analysis
            </Button>

            <div className="mt-auto grid gap-4 pt-8 md:grid-cols-3 xl:absolute xl:bottom-4 xl:left-14 xl:right-14 xl:h-[94px] xl:gap-3 xl:pt-0">
              <div className="relative min-h-32 overflow-hidden rounded-[1.6rem] border border-emerald-900/10 bg-white/95 p-5 shadow-[0_10px_24px_rgba(28,66,45,0.14)] backdrop-blur-sm xl:h-full xl:min-h-0 xl:rounded-2xl xl:p-3">
                <div className="absolute -bottom-12 -left-8 h-20 w-64 rounded-[50%] bg-lime-300/55 blur-sm" />
                <p className="relative text-[11px] font-extrabold uppercase tracking-[0.14em] text-[#247a58] md:text-sm">Priority signal</p>
                <div className="relative mt-5 flex flex-wrap items-center justify-between gap-3 xl:mt-1">
                  <span className="font-heading text-xl font-bold text-[#123f31] xl:text-base">{priorityReading?.metric.name || "Awaiting analysis"}</span>
                  {priorityReading && <MetricStatusBadge metricKey={priorityReading.metric.key} value={priorityReading.value} />}
                </div>
              </div>

              <div className="relative min-h-32 overflow-hidden rounded-[1.6rem] border border-emerald-900/10 bg-white/95 p-5 shadow-[0_10px_24px_rgba(28,66,45,0.14)] backdrop-blur-sm xl:h-full xl:min-h-0 xl:rounded-2xl xl:p-3">
                <div className="absolute -bottom-14 right-0 h-24 w-72 rounded-[50%] bg-lime-300/40 blur-sm" />
                <p className="relative text-[11px] font-extrabold uppercase tracking-[0.14em] text-[#247a58] md:text-sm">Analysed area</p>
                <p className="relative mt-4 font-heading text-4xl font-bold text-[#123f31] xl:mt-1 xl:text-2xl">
                  {farm?.area_acres ? pretty(farm.area_acres, 2) : "--"}
                  <span className="ml-2 text-base font-medium text-[#709488]">acres</span>
                </p>
              </div>

              <div className="relative min-h-32 overflow-hidden rounded-[1.6rem] border border-emerald-900/10 bg-white/95 p-5 shadow-[0_10px_24px_rgba(28,66,45,0.14)] backdrop-blur-sm xl:h-full xl:min-h-0 xl:rounded-2xl xl:p-3">
                <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-[#247a58] md:text-sm">Coverage</p>
                <p className="mt-4 font-heading text-4xl font-bold text-[#123f31] xl:mt-1 xl:text-2xl">
                  {displayCells.length || "--"}
                  <span className="ml-2 text-base font-medium text-[#709488]">land cells</span>
                </p>
                <div className="absolute bottom-5 right-5 grid grid-cols-4 gap-1 xl:bottom-3 xl:right-3">
                  {Array.from({ length: 12 }, (_, index) => (
                    <span key={index} className={`h-4 w-4 rounded-[4px] xl:h-3 xl:w-3 ${index > 8 ? "bg-[#246b4e]" : index > 5 ? "bg-emerald-300" : "bg-emerald-100"}`} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {loading && <div className="rounded-3xl border border-emerald-100 bg-white p-6 text-sm text-slate-500 shadow-sm">Loading land intelligence...</div>}
        {error && <div className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}

        <StatStrip
          desktopColumnsClass="lg:grid-cols-6"
          items={stats.map((item) => ({ ...item, icon: item.label === "Cloud cover" ? Cloud : item.label === "Valid pixels" ? Waves : item.label === "Farm area" ? Mountain : item.label === "H3 cells" ? Hexagon : item.label === "Latest scene" ? RefreshCw : Leaf }))}
        />

        <PipelineStepper steps={["Location", "Farmer", "Boundary", "Grid", "Satellite", "Raster", "Intelligence"]} currentStep={7} />

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,0.55fr)]">
        <div className="space-y-4">
          <div className="overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white shadow-[0_18px_55px_rgba(15,23,42,0.08)]">
            <div className="border-b border-slate-100 bg-slate-50/70 px-4 py-4 md:px-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="flex items-center gap-2 text-sm font-bold text-slate-950"><ScanLine className="h-4 w-4 text-emerald-700" /> Land health map</p>
                  <p className="mt-0.5 text-xs text-slate-500">Viewing {selectedParameterInfo?.name || selectedParameter}</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="rounded-full bg-emerald-50 px-3 py-1 font-semibold text-emerald-700">Visual grid</span>
                  {canViewTechnicalH3Layer(user) && (
                    <button
                      type="button"
                      onClick={() => setShowH3((value) => !value)}
                      className={`rounded-full px-3 py-1 font-semibold transition ${h3Enabled ? "bg-sky-50 text-sky-700" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}
                    >
                      H3 {h3Enabled ? "on" : "off"}
                    </button>
                  )}
                </div>
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
                {PARAMETERS.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setSelectedParameter(item.key)}
                    className={`shrink-0 rounded-xl border px-3 py-2 text-left transition ${selectedParameter === item.key ? "border-emerald-800 bg-emerald-900 text-white shadow-md" : "border-slate-200 bg-white text-slate-600 hover:border-emerald-200 hover:bg-emerald-50"}`}
                  >
                    <span className="block text-[11px] font-semibold">{item.name}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="p-3 md:p-4">
              <LandGridMap
                farm={farm}
                gridCells={displayCells}
                gridValues={gridValues}
                h3Cells={h3Enabled ? h3Cells : []}
                selectedParameter={selectedParameter}
                onGridCellClick={setSelectedCell}
                selectedGridCellId={displaySelected?.grid_cell_id}
                showH3Layer={h3Enabled}
                userRole={user?.role}
              />
            </div>
          </div>

          <div className="overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white shadow-[0_14px_40px_rgba(15,23,42,0.06)]">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
              <div>
                <p className="text-sm font-bold text-slate-950">Cell-by-cell readings</p>
                <p className="text-xs text-slate-500">Select a row to inspect its full analysis</p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-bold text-slate-600">{displayCells.length || 0} cells</span>
            </div>
            <div className="max-h-96 overflow-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur">
                  <tr className="text-[10px] uppercase tracking-wider text-slate-500">
                    <th className="px-4 py-3">Cell</th>
                    <th className="px-3 py-3">{selectedParameterInfo?.name || "Reading"}</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="hidden px-3 py-3 sm:table-cell">Crop Moisture</th>
                    <th className="hidden px-3 py-3 md:table-cell">Bare Land</th>
                  </tr>
                </thead>
                <tbody>
                  {displayCells.map((cell, index) => (
                    <tr key={cell.grid_cell_id || index} onClick={() => setSelectedCell(cell)} className={`cursor-pointer border-t border-slate-100 transition hover:bg-emerald-50/70 ${displaySelected?.grid_cell_id === cell.grid_cell_id ? "bg-emerald-50" : ""}`}>
                      <td className="px-4 py-3 font-bold text-slate-800">{String(index + 1).padStart(2, "0")}</td>
                      <td className="px-3 py-3 font-semibold text-slate-900">
                        {getLandMetric(selectedParameter)
                          ? <MetricInterpretationText metricKey={selectedParameter} value={valueFor(cell, selectedParameter)} className="font-semibold" />
                          : pretty(valueFor(cell, selectedParameter), selectedParameter === "temperature" ? 1 : 3)}
                      </td>
                      <td className="px-3 py-3">
                        {getLandMetric(selectedParameter)
                          ? <MetricStatusBadge metricKey={selectedParameter} value={valueFor(cell, selectedParameter)} compact />
                          : <span className="text-slate-400">Raw reading</span>}
                      </td>
                      <td className="hidden px-3 py-3 sm:table-cell"><MetricInterpretationText metricKey="ndmi" value={valueFor(cell, "ndmi")} className="font-medium" /></td>
                      <td className="hidden px-3 py-3 md:table-cell"><MetricInterpretationText metricKey="bsi" value={valueFor(cell, "bsi")} className="font-medium" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white shadow-[0_14px_45px_rgba(15,23,42,0.07)] xl:sticky xl:top-5">
            <div className="border-b border-slate-100 bg-[#f8faf7] px-5 py-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-700">{displaySelected ? "Selected land cell" : "Farm snapshot"}</p>
                  <h2 className="mt-1 font-heading text-xl font-bold text-slate-950">{displaySelected ? `Cell ${displaySelected.grid_row ?? "-"} / ${displaySelected.grid_col ?? "-"}` : "Latest field reading"}</h2>
                </div>
                <span className="grid h-10 w-10 place-items-center rounded-2xl bg-emerald-900 text-white"><Activity className="h-5 w-5" /></span>
              </div>
              {displaySelected && (
                <div className="mt-3 flex items-center justify-between gap-3 text-[10px] text-slate-500">
                  <span className="truncate font-mono">{displaySelected.grid_cell_id}</span>
                  <button type="button" onClick={() => setSelectedCell(null)} className="shrink-0 font-semibold text-emerald-700 hover:text-emerald-900">Show farm summary</button>
                </div>
              )}
            </div>

            <div className="p-4 md:p-5">
              {displaySelected ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    {LAND_METRICS.map((metric) => (
                      <MetricReading
                        key={metric.key}
                        metricKey={metric.key}
                        value={selectedDetails?.weighted_average?.[metric.backendKey] ?? metricValueFromCell(displaySelected, metric.key)}
                        compact
                      />
                    ))}
                  </div>

                  <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
                    <div className="flex items-start gap-3">
                      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-emerald-900 text-white"><Sparkles className="h-4 w-4" /></span>
                      <div>
                        <p className="text-xs font-bold text-emerald-950">Field interpretation</p>
                        <p className="mt-1 text-xs leading-5 text-emerald-900/70">{recommendationFor(selectedDetails?.latest_values || displaySelected)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      ["Temperature", selectedDetails?.weighted_average?.surface_temp_c ?? displaySelected.surface_temp_c, "C"],
                      ["Cloud cover", selectedDetails?.weighted_average?.cloud_percentage ?? displaySelected.cloud_percentage, "%"],
                      ["Valid pixels", selectedDetails?.weighted_average?.valid_pixel_percentage ?? displaySelected.valid_pixel_percentage, "%"],
                    ].map(([label, value, unit]) => (
                      <div key={label} className="rounded-2xl bg-slate-50 p-3">
                        <p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">{label}</p>
                        <p className="mt-1 font-heading text-lg font-bold text-slate-800">{pretty(value, 1)}<span className="ml-0.5 text-[10px] text-slate-400">{unit}</span></p>
                      </div>
                    ))}
                  </div>

                  {(selectedDetails?.h3_contributions || []).length > 0 && (
                    <div className="rounded-2xl border border-slate-100 bg-white p-3">
                      <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">Technical H3 contributions</div>
                      <div className="space-y-2">
                        {(selectedDetails?.h3_contributions || []).slice(0, 6).map((row) => (
                          <div key={row.h3_index} className="rounded-xl border border-slate-100 bg-slate-50/70 p-2 text-xs">
                            <div className="flex items-center justify-between gap-2">
                              <span className="truncate font-mono text-[10px] text-slate-500">{String(row.h3_index)}</span>
                              <span className="font-semibold text-slate-800">{row.overlap_percentage}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                    <p className="text-xs font-semibold text-slate-800">Select any square on the map</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">You will see its raw readings translated into Crop Greenness, Crop Moisture, Water Stress, Crop Nutrition and other practical signals.</p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {[
                      ["Cloud cover", `${pretty(latestSummary.avg_cloud_percentage, 0)}%`],
                      ["Valid pixels", `${pretty(latestSummary.valid_pixel_percentage, 0)}%`],
                      ["Farm H3 cells", latestSummary.total_farm_h3_cells ?? latestSummary.total_h3_cells ?? h3Cells.length ?? "--"],
                      ["Processed H3", latestSummary.processed_h3_cells ?? latestSummary.latest_processed_h3_cells ?? "--"],
                      ["Grid cells", latestSummary.total_grid_cells ?? displayCells.length ?? "--"],
                      ["Cells with values", latestSummary.grid_cells_with_values ?? displayCells.length ?? "--"],
                    ].map(([label, value]) => (
                      <div key={label} className="rounded-2xl border border-slate-100 p-3">
                        <span className="block text-[10px] font-semibold uppercase tracking-wide text-slate-400">{label}</span>
                        <span className="mt-1 block font-heading text-lg font-bold text-slate-900">{value}</span>
                      </div>
                    ))}
                  </div>

                  {!hasAnalysis && <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">Analysis is not available yet. Run the latest analysis to create the first reading.</div>}
                  {Number(latestSummary.total_grid_cells || displayCells.length || 0) > 0 && Number(latestSummary.grid_cells_with_values || 0) === 0 && <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">The land grid exists, but satellite values have not been computed yet.</div>}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
      </div>
    </Motion.div>
  );
}
