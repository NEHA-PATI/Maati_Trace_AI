import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Activity, ArrowLeft, CalendarDays, ChevronRight, CloudSun,
  Droplets, Gauge, Layers, LayoutGrid, Leaf, MapPin, Mountain, RefreshCw,
  Ruler, Sparkles, Sprout, Sun, TrendingUp, Waves, X,
} from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import PipelineGlassLoader from "@/components/ui-custom/PipelineGlassLoader";
import LandGridMap from "@/components/ui-custom/LandGridMap";
import {
  buildFieldInterpretation,
  interpretLandMetric,
  LAND_METRICS,
  METRIC_STATUSES,
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

const METRIC_ICONS = {
  ndvi: Leaf,
  evi: TrendingUp,
  savi: Sprout,
  ndmi: Droplets,
  ndwi: Waves,
  msi: Gauge,
  ndre: Sparkles,
  bsi: Mountain,
  nbr: Activity,
};

const STATUS_PRIORITY = {
  critical: 5,
  needs_attention: 4,
  watch: 3,
  good: 2,
  excellent: 1,
  unavailable: 0,
};

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
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function skyLabel(cloud) {
  if (cloud === null || cloud === undefined || cloud === "" || Number.isNaN(Number(cloud))) return "Sky not recorded";
  const value = Number(cloud);
  if (value < 15) return "Sky was clear";
  if (value < 40) return "Some clouds that day";
  return "Cloudy that day";
}

function imageQualityLabel(validPct) {
  if (validPct === null || validPct === undefined || Number.isNaN(Number(validPct))) return "Not recorded";
  const value = Number(validPct);
  if (value >= 80) return "Good picture";
  if (value >= 50) return "Partial picture";
  return "Poor picture";
}

function worstReading(readings) {
  return [...readings]
    .filter((r) => r.result.status !== "unavailable")
    .sort((a, b) => STATUS_PRIORITY[b.result.status] - STATUS_PRIORITY[a.result.status])[0];
}

function Reveal({ children, delay = 0, className = "" }) {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </Motion.div>
  );
}

function StatusBadge({ result, short = false, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${result.badgeClass} ${className}`}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: result.color }} />
      {short ? result.shortLabel : result.label}
    </span>
  );
}

export default function LandIntelligence() {
  const { farmId } = useParams();
  const navigate = useNavigate();
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
  const statusPriority = STATUS_PRIORITY;
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
        end_date: new Date().toISOString().slice(0, 10),
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

  // ---- derived, presentation-only ------------------------------------------
  const locationLine = [farm?.village_name, farm?.block_name, farm?.district_name].filter(Boolean).join(", ") || "Location pending";
  const cloudValue = latestSentinel?.cloud_percentage ?? latestSummary.avg_cloud_percentage;
  const validValue = latestSummary.valid_pixel_percentage ?? latestSentinel?.valid_pixels_pct;

  const selectedIndex = displaySelected
    ? displayCells.findIndex((cell) => String(cell.grid_cell_id) === String(displaySelected.grid_cell_id))
    : -1;

  const cellMetricReadings = LAND_METRICS.map((metric) => {
    const value = displaySelected
      ? (selectedDetails?.weighted_average?.[metric.backendKey] ?? metricValueFromCell(displaySelected, metric.key))
      : metricValueFromSummary(latestSummary, metric.key);
    return { metric, value, result: interpretLandMetric(metric.key, value) };
  });
  const worstCellReading = worstReading(cellMetricReadings);
  const priorityForBanner = displaySelected ? worstCellReading : priorityReading;

  const cellExtras = [
    {
      label: "Warmth",
      icon: Sun,
      value: pretty(selectedDetails?.weighted_average?.surface_temp_c ?? displaySelected?.surface_temp_c ?? latestSummary.avg_surface_temp_c, 1),
      suffix: "°C",
      tint: "bg-[var(--mt-gold-tint)] text-[var(--mt-gold-text)]",
    },
    {
      label: "Sky",
      icon: CloudSun,
      value: skyLabel(selectedDetails?.weighted_average?.cloud_percentage ?? displaySelected?.cloud_percentage ?? cloudValue),
      suffix: "",
      tint: "bg-[var(--mt-sky-tint)] text-[var(--mt-sky-text)]",
    },
    {
      label: "Picture",
      icon: Layers,
      value: imageQualityLabel(selectedDetails?.weighted_average?.valid_pixel_percentage ?? displaySelected?.valid_pixel_percentage ?? validValue),
      suffix: "",
      tint: "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]",
    },
  ];

  const fieldInterpretationText = buildFieldInterpretation(cellMetricReadings, {
    cloudPercentage:
      selectedDetails?.weighted_average?.cloud_percentage ?? displaySelected?.cloud_percentage ?? cloudValue,
  });

  const facts = [
    { icon: Ruler, tint: "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]", value: farm?.area_acres ? `${pretty(farm.area_acres, 2)} ac` : "—", label: "Farm Area" },
    { icon: LayoutGrid, tint: "bg-[var(--mt-sky-tint)] text-[var(--mt-sky-text)]", value: displayCells.length ? String(displayCells.length) : "Not yet", label: "Zones Checked" },
    { icon: CalendarDays, tint: "bg-[var(--mt-gold-tint)] text-[var(--mt-gold-text)]", value: latestSceneDate ? formatDate(latestSceneDate) : "Not yet", label: "Last Check" },
  ];

  // Shared body of the selected-cell / farm-summary panel (desktop aside + mobile sheet).
  const panelBody = () => (
    <>
      <div className="text-[10.5px] font-extrabold uppercase tracking-[0.08em] text-[var(--mt-leaf-deep)]">
        {displaySelected ? "Selected land cell" : "Farm summary"}
      </div>
      <div className="mt-1 flex items-center justify-between gap-3">
        <div className="text-[18px] font-extrabold text-[var(--mt-ink)]">
          {displaySelected
            ? (selectedIndex >= 0 ? `Cell ${selectedIndex + 1} of ${displayCells.length}` : "This cell")
            : "Whole farm"}
        </div>
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[var(--mt-leaf-deep)] text-white">
          <Activity className="h-4 w-4" strokeWidth={2.2} />
        </span>
      </div>
      {displaySelected && (
        <button
          type="button"
          onClick={() => setSelectedCell(null)}
          className="mt-2 inline-flex items-center gap-1 text-[12px] font-bold text-[var(--mt-leaf-deep)]"
        >
          <ChevronRight className="h-3.5 w-3.5 rotate-180" strokeWidth={2.6} />
          Show whole farm
        </button>
      )}

      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {cellMetricReadings.map(({ metric, result }) => (
          <div key={metric.key} className={`rounded-[14px] border p-3 ${result.surfaceClass}`}>
            <div className="flex flex-wrap items-start justify-between gap-x-2 gap-y-1">
              <span className="min-w-0 text-[11.5px] font-bold leading-tight text-[var(--mt-ink)]">{metric.name}</span>
              <StatusBadge result={result} short className="shrink-0" />
            </div>
            <div className={`mt-2 text-[13px] font-extrabold leading-tight ${result.textClass}`}>{result.headline}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-[var(--mt-radius-md)] bg-[var(--mt-leaf-tint)] p-4">
        <div className="flex items-center gap-2 text-[12.5px] font-extrabold text-[var(--mt-leaf-deep)]">
          <Sparkles className="h-4 w-4" strokeWidth={2.2} />
          Field interpretation
        </div>
        <p className="mt-1.5 text-[12.5px] font-semibold leading-relaxed text-[var(--mt-ink)]">{fieldInterpretationText}</p>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2">
        {cellExtras.map((extra) => (
          <div key={extra.label} className={`rounded-[12px] px-2.5 py-2 ${extra.tint}`}>
            <div className="flex items-center gap-1 text-[10px] font-extrabold uppercase tracking-wide">
              <extra.icon className="h-3 w-3" strokeWidth={2.4} />
              {extra.label}
            </div>
            <div className="mt-1 text-[12px] font-extrabold text-[var(--mt-ink)]">
              {extra.value}{extra.suffix}
            </div>
          </div>
        ))}
      </div>

      {!hasAnalysis && (
        <div className="mt-3 rounded-[12px] bg-[var(--mt-gold-tint)] p-3 text-[12px] font-semibold text-[var(--mt-gold-text)]">
          This field has not been checked yet. Tap &ldquo;Check Again&rdquo; to run the first check.
        </div>
      )}
    </>
  );

  return (
    <Motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-surface">
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

      {/* ── page header ─────────────────────────────────────────────────── */}
      <header className="sticky top-16 z-20 flex items-center gap-3 border-b border-[var(--mt-line)] bg-white/95 px-4 py-3 backdrop-blur-md md:px-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="flex h-11 items-center gap-1.5 rounded-full bg-[var(--mt-paper-warm)] px-3 text-[13px] font-bold text-[var(--mt-ink)]"
        >
          <ArrowLeft className="h-4 w-4" strokeWidth={2.4} />
          Back
        </button>
        <div className="min-w-0 flex-1">
          <div className="truncate text-[16px] font-extrabold text-[var(--mt-ink)]">{farm?.farm_name || "Your farm"}</div>
          <div className="truncate text-[12px] font-semibold text-[var(--mt-ink-soft)]">{locationLine}</div>
        </div>
        <button
          type="button"
          onClick={runLatestAnalysis}
          disabled={refreshing}
          className="flex h-11 items-center gap-2 rounded-full bg-[var(--mt-leaf)] px-4 text-[13px] font-bold text-white disabled:opacity-60"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} strokeWidth={2.4} />
          <span className="hidden sm:inline">Check Again</span>
        </button>
      </header>

      <div className="mx-auto max-w-[1320px] space-y-4 p-4 md:p-6">

        {loading && (
          <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-6 text-sm font-semibold text-[var(--mt-ink-soft)]">
            Checking your field…
          </div>
        )}
        {error && (
          <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-clay)]/30 bg-[var(--mt-clay-tint)] p-4 text-sm font-semibold text-[var(--mt-clay-text)]">
            {error}
          </div>
        )}

        {/* ── hero ─────────────────────────────────────────────────────── */}
        <Reveal>
          <section
            className="relative overflow-hidden rounded-[var(--mt-radius-lg)] p-5 md:p-7"
            style={{ background: "linear-gradient(135deg,#EAF3DD,#DCEDCB)" }}
          >
            <div className="relative z-10">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/75 px-3 py-1 text-[11.5px] font-extrabold text-[var(--mt-leaf-deep)]">
                <MapPin className="h-3.5 w-3.5" strokeWidth={2.4} />
                Field Check
              </span>
              <h1 className="mt-3 text-[24px] font-extrabold text-[var(--mt-ink)] md:text-[27px]">{farm?.farm_name || "Your farm"}</h1>
              <div className="mt-1 flex items-center gap-1.5 text-[13.5px] font-bold text-[var(--mt-leaf-deep)]">
                <MapPin className="h-3.5 w-3.5 shrink-0" strokeWidth={2.2} />
                <span className="truncate">{locationLine}</span>
              </div>
              <div className="mt-3.5 flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-[12.5px] font-bold text-[var(--mt-ink)]">
                  <CalendarDays className="h-3.5 w-3.5" strokeWidth={2.2} />
                  {latestSceneDate ? `Checked ${formatDate(latestSceneDate)}` : "Not checked yet"}
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-[12.5px] font-bold text-[var(--mt-ink)]">
                  <CloudSun className="h-3.5 w-3.5" strokeWidth={2.2} />
                  {skyLabel(cloudValue)}
                </span>
              </div>
            </div>
            <svg className="pointer-events-none absolute inset-x-0 bottom-0 h-14 w-full opacity-90" viewBox="0 0 1000 70" preserveAspectRatio="none" aria-hidden>
              <path d="M0 70V35 Q150 12 350 30 T700 20 T1000 35V70Z" fill="#CFE3B8" />
              <path d="M0 70V50 Q250 35 500 50 T1000 46V70Z" fill="#B7D89D" />
            </svg>
          </section>
        </Reveal>

        {/* ── priority banner ──────────────────────────────────────────── */}
        {priorityForBanner && (
          <Reveal delay={0.05}>
            <div className={`flex items-center gap-4 rounded-[var(--mt-radius-md)] border p-4 md:px-5 ${priorityForBanner.result.surfaceClass}`}>
              <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-white">
                {(() => {
                  const Icon = METRIC_ICONS[priorityForBanner.metric.key] || Activity;
                  return <Icon className="h-5 w-5" style={{ color: priorityForBanner.result.color }} strokeWidth={2.2} />;
                })()}
              </span>
              <div className="min-w-0">
                <div className={`text-[15px] font-extrabold ${priorityForBanner.result.textClass}`}>{priorityForBanner.result.banner}</div>
                {priorityForBanner.result.tip && (
                  <div className={`mt-0.5 text-[13px] font-semibold ${priorityForBanner.result.textClass} opacity-90`}>{priorityForBanner.result.tip}</div>
                )}
              </div>
            </div>
          </Reveal>
        )}

        {/* ── facts ────────────────────────────────────────────────────── */}
        <Reveal delay={0.08}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {facts.map((fact) => (
              <div key={fact.label} className="flex items-center gap-3 rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white px-4 py-4">
                <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${fact.tint}`}>
                  <fact.icon className="h-5 w-5" strokeWidth={2.1} />
                </span>
                <div className="min-w-0">
                  <div className="truncate text-[18px] font-extrabold text-[var(--mt-ink)]">{fact.value}</div>
                  <div className="mt-0.5 text-[12.5px] font-bold text-[var(--mt-ink-soft)]">{fact.label}</div>
                </div>
              </div>
            ))}
          </div>
        </Reveal>

        {/* ── map + selected cell ──────────────────────────────────────── */}
        <h2 className="flex items-center gap-2 pt-2 text-[16.5px] font-extrabold text-[var(--mt-ink)]">
          <Layers className="h-[18px] w-[18px]" strokeWidth={2.1} />
          Land Health Map
        </h2>

        <div className="grid gap-4 xl:grid-cols-[1fr_380px] xl:items-start">
          {/* map card */}
          <Reveal className="overflow-hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white">
            <div className="flex flex-wrap items-center justify-between gap-2 px-4 pt-4 md:px-5">
              <p className="text-[12.5px] font-semibold text-[var(--mt-ink-soft)]">
                Viewing: <b className="text-[var(--mt-ink)]">{selectedParameterInfo?.name || selectedParameter}</b>
              </p>
              {canViewTechnicalH3Layer(user) && (
                <button
                  type="button"
                  onClick={() => setShowH3((value) => !value)}
                  className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11.5px] font-bold ${
                    h3Enabled ? "bg-[var(--mt-sky-tint)] text-[var(--mt-sky-text)]" : "bg-[var(--mt-paper-warm)] text-[var(--mt-ink-soft)]"
                  }`}
                >
                  <Layers className="h-3.5 w-3.5" strokeWidth={2.2} />
                  Detailed grid {h3Enabled ? "on" : "off"}
                </button>
              )}
            </div>

            <div className="flex gap-2 overflow-x-auto px-4 py-3 scrollbar-hide md:px-5">
              {PARAMETERS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setSelectedParameter(item.key)}
                  className={`shrink-0 rounded-[var(--mt-radius-sm)] border px-3.5 py-2 text-[12px] font-bold transition ${
                    selectedParameter === item.key
                      ? "border-[var(--mt-leaf-deep)] bg-[var(--mt-leaf-deep)] text-white"
                      : "border-[var(--mt-line)] bg-white text-[var(--mt-ink)]"
                  }`}
                >
                  {item.name}
                </button>
              ))}
            </div>

            <div className="px-3 pb-3 md:px-4">
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

            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-[var(--mt-line)] px-4 py-3.5 md:px-5">
              {Object.values(METRIC_STATUSES).map((status) => (
                <span key={status.label} className="flex items-center gap-1.5 text-[12px] font-bold text-[var(--mt-ink)]">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: status.color }} />
                  {status.shortLabel}
                </span>
              ))}
            </div>
          </Reveal>

          {/* selected cell / farm summary — desktop aside */}
          <Reveal delay={0.05} className="hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-4 md:p-5 xl:sticky xl:top-32 xl:block">
            {panelBody()}
          </Reveal>
        </div>

        {/* mobile — farm summary stays inline; a picked cell opens as a sheet */}
        {!displaySelected && (
          <Reveal delay={0.05} className="rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-4 xl:hidden">
            {panelBody()}
          </Reveal>
        )}

        <AnimatePresence>
          {displaySelected && (
            <div className="fixed inset-0 z-[60] flex items-end xl:hidden">
              <Motion.div
                className="absolute inset-0 bg-black/40"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedCell(null)}
              />
              <Motion.div
                className="relative max-h-[86vh] w-full overflow-y-auto rounded-t-[24px] bg-white px-4 pb-10 pt-3"
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={{ type: "spring", stiffness: 320, damping: 34 }}
              >
                <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-[var(--mt-line)]" />
                <button
                  type="button"
                  onClick={() => setSelectedCell(null)}
                  className="mb-2 ml-auto flex h-10 items-center gap-1.5 rounded-full bg-[var(--mt-paper-warm)] px-3.5 text-[13px] font-bold text-[var(--mt-ink)]"
                >
                  <X className="h-4 w-4" strokeWidth={2.4} />
                  Close
                </button>
                {panelBody()}
              </Motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* ── every signal explained (follows the picked cell) ─────────── */}
        <div className="pt-2">
          <h2 className="flex items-center gap-2 text-[16.5px] font-extrabold text-[var(--mt-ink)]">
            <Sparkles className="h-[18px] w-[18px]" strokeWidth={2.1} />
            Every Signal, Explained
          </h2>
          <p className="mt-1 text-[12.5px] font-semibold text-[var(--mt-ink-soft)]">
            {displaySelected ? "For the cell you picked on the map" : "Across the whole farm"}
          </p>
        </div>
        <Motion.div
          key={displaySelected ? `cell-${displaySelected.grid_cell_id}` : "farm"}
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.05 } } }}
          initial="hidden"
          animate="show"
          className="overflow-hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white"
        >
          {cellMetricReadings.map(({ metric, result }) => {
            const Icon = METRIC_ICONS[metric.key] || Activity;
            return (
              <Motion.div
                key={metric.key}
                variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.35 } } }}
                className="flex flex-col gap-3 border-b border-[var(--mt-line)] p-4 last:border-b-0 md:flex-row md:items-start md:gap-5 md:px-5"
                style={{ borderLeft: `4px solid ${result.color}` }}
              >
                <div className="flex items-center gap-3 md:w-[240px] md:shrink-0">
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-[11px] ${result.surfaceClass}`}>
                    <Icon className="h-4 w-4" style={{ color: result.color }} strokeWidth={2.2} />
                  </span>
                  <div className="min-w-0">
                    <div className="text-[14px] font-extrabold text-[var(--mt-ink)]">{metric.name}</div>
                    <StatusBadge result={result} className="mt-1" />
                  </div>
                </div>
                <p className="text-[13.5px] font-semibold leading-relaxed text-[var(--mt-ink)]">{result.paragraph}</p>
              </Motion.div>
            );
          })}
        </Motion.div>
      </div>
    </Motion.div>
  );
}
