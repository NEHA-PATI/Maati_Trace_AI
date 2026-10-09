import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Activity, ArrowLeft, CalendarDays, ChevronRight,
  Droplets, Layers, Leaf, MapPin, Mountain, RefreshCw,
  Sparkles, Sprout, Sun, TrendingUp, Waves, X,
} from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import HexagonPipelineLoader from "@/components/ui-custom/HexagonPipelineLoader";
import LandGridMap from "@/components/ui-custom/LandGridMap";
import { getFarm } from "@/lib/api/farm";
import {
  getFarmGridCellDetails,
  getGridCellCalculations,
  getFarmGridCells,
  getFarmH3Cells,
  getLatestFarmCalculations,
  getLatestGridCalculations,
  getLatestGridValues,
  getMetricContent,
} from "@/lib/api/analytics";
import {
  buildCalculatedFieldInterpretation,
  CALCULATED_METRICS,
  interpretCalculatedMetric,
} from "@/features/land-intelligence/calculatedMetrics";
import {
  getLatestAnalysisStatus,
  runLatestAnalysis as triggerLatestAnalysis,
  ANALYSIS_PIPELINE_STEPS,
} from "@/lib/api/hotStream";
import { canViewTechnicalH3Layer } from "@/shared/rbac/permissions";
import { getStoredUser } from "@/features/auth/session";
import { getFarmerFpoRelationships } from "@/lib/api/fpo";

const PARAMETERS = [
  ...CALCULATED_METRICS.map((metric) => ({ key: metric.key, name: metric.name })),
];

const REGISTRATION_PIPELINE_STEPS = [
  "Validate farmer, crop and boundary",
  "Validate farm location",
  "Generate H3 hexagons",
  "Save farm record and polygon",
  "Start complete analysis",
];
const ANALYSIS_STEPS = ANALYSIS_PIPELINE_STEPS.map(([, label]) => label);
const BOOTSTRAP_STEPS = [...REGISTRATION_PIPELINE_STEPS, ...ANALYSIS_STEPS];

function analysisProgress(status, offset = 0) {
  const terminal = ["completed", "completed_with_warnings", "succeeded", "failed"].includes(status?.status);
  if (terminal) {
    const finalStep = offset + ANALYSIS_PIPELINE_STEPS.length - 1;
    return {
      step: finalStep,
      label: status.status === "failed" ? "Analysis failed" : "Build crop intelligence",
      details: [`Status: ${status.status}`],
    };
  }
  const current = status?.current_stage;
  const rows = Array.isArray(status?.stages) ? status.stages : [];
  const index = ANALYSIS_PIPELINE_STEPS.findIndex(([key]) => key === current);
  let step = offset + (index >= 0 ? index : 0);
  let label = (offset ? BOOTSTRAP_STEPS : ANALYSIS_STEPS)[step] || "Running analysis";
  let details = current ? [`Status: ${status?.status || "running"}`] : [];
  const environment = rows.find((row) => row.name === "environment_datasets");
  const datasets = environment?.details?.datasets || [];
  if (current === "environment_datasets" && datasets.length) {
    const active = datasets.findIndex((row) => row.status === "running");
    const completed = datasets.filter((row) => ["succeeded", "cached", "completed_with_warnings"].includes(row.status)).length;
    const datasetIndex = active >= 0 ? active : Math.min(completed, ANALYSIS_PIPELINE_STEPS.length - 2);
    step = offset + 1 + datasetIndex;
    label = (offset ? BOOTSTRAP_STEPS : ANALYSIS_STEPS)[step] || label;
    details = [`Datasets: ${completed}/${datasets.length} complete`];
    if (active >= 0) details.push(`Current: ${datasets[active].dataset_key}`);
  }
  return { step, label, details };
}

const CALCULATED_METRIC_ICONS = {
  crop_condition: Sprout,
  water_stress: Droplets,
  moisture_condition: Waves,
  growth_condition: TrendingUp,
  growth_anomaly: Activity,
  heat_stress: Sun,
  waterlogging_risk: Waves,
  soil_condition: Mountain,
  nutrient_stress_risk: Leaf,
  erosion_risk: Mountain,
};

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.items || payload?.data || payload?.grid_cells || payload?.grid_values || payload?.h3_cells || [];
}

function formatDate(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function metricDisplayName(metric, content) {
  const configured = Array.isArray(content)
    ? content.find((item) => item.metric_key === metric.key)
    : null;
  return configured?.display_name || configured?.displayName || metric.name;
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
  const location = useLocation();
  const navigate = useNavigate();
  const user = getStoredUser();
  const enteredFromBootstrap = location.state?.pipelineMode === "bootstrap";
  const [pipelineMode, setPipelineMode] = useState(
    enteredFromBootstrap ? "bootstrap" : "incremental_latest",
  );
  const pipelineOffset = pipelineMode === "bootstrap" ? REGISTRATION_PIPELINE_STEPS.length : 0;
  const pipelineSteps = pipelineMode === "bootstrap" ? BOOTSTRAP_STEPS : ANALYSIS_STEPS;
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [farm, setFarm] = useState(null);
  const [farmFpoRelationships, setFarmFpoRelationships] = useState([]);
  const [metricContent, setMetricContent] = useState([]);
  const [gridCells, setGridCells] = useState([]);
  const [gridValues, setGridValues] = useState([]);
  const [gridCalculations, setGridCalculations] = useState([]);
  const [farmCalculations, setFarmCalculations] = useState([]);
  const [h3Cells, setH3Cells] = useState([]);
  const [selectedParameter, setSelectedParameter] = useState("crop_condition");
  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [showH3, setShowH3] = useState(false);
  const [pipelineOpen, setPipelineOpen] = useState(enteredFromBootstrap);
  const [pipelineStage, setPipelineStage] = useState(pipelineOffset);
  const [pipelineStatus, setPipelineStatus] = useState("");
  const [pipelineFailure, setPipelineFailure] = useState("");
  const [pipelineWarning, setPipelineWarning] = useState("");
  const [pipelineDetails, setPipelineDetails] = useState([]);
  const [analysisStatus, setAnalysisStatus] = useState(null);
  const manualRunRef = useRef(false);

  function updatePipelineStage(stage, status, details = []) {
    setPipelineStage(stage);
    setPipelineStatus(status);
    setPipelineDetails(details.filter(Boolean));
  }

  async function loadLandIntelligence(statusSnapshot = analysisStatus) {
    const completedResultDate = statusSnapshot?.latest_completed_run?.result_date
      ? String(statusSnapshot.latest_completed_run.result_date).slice(0, 10)
      : "";
    const [farmPayload, gridCellsPayload, gridValuesPayload, h3Payload, gridCalculationsPayload, farmCalculationsPayload] = await Promise.all([
      getFarm(farmId),
      getFarmGridCells(farmId).catch(() => []),
      getLatestGridValues(farmId).catch(() => []),
      getFarmH3Cells(farmId).catch(() => []),
      getLatestGridCalculations(farmId, completedResultDate).catch(() => []),
      getLatestFarmCalculations(farmId, "farm", completedResultDate).catch(() => []),
    ]);

    console.log("FARM", farmPayload);
    console.log("GRID_CELLS", gridCellsPayload);
    console.log("H3_CELLS", h3Payload);

    setFarm(farmPayload);
    setMetricContent(await getMetricContent(farmPayload?.crop_code || "").catch(() => []));
    setGridCells(normalizeList(gridCellsPayload));
    setGridValues(normalizeList(gridValuesPayload));
    setGridCalculations(normalizeList(gridCalculationsPayload));
    setFarmCalculations(normalizeList(farmCalculationsPayload));
    setH3Cells(normalizeList(h3Payload));
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    // Read the run state before analytics. Existing latest rows may belong to
    // the previous completed run while a new source materialization is still
    // in progress; retaining that distinction prevents stale results from
    // being presented as the active run's output.
    getLatestAnalysisStatus(farmId)
      .catch(() => null)
      .then((status) => {
        if (!cancelled) setAnalysisStatus(status);
        return loadLandIntelligence(status);
      })
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
    if (user?.role !== "farmer") return;
    let cancelled = false;
    getFarmerFpoRelationships()
      .then((rows) => {
        if (!cancelled) setFarmFpoRelationships((Array.isArray(rows) ? rows : rows?.items || []).filter((row) => String(row.farm_id) === String(farmId)));
      })
      .catch(() => { if (!cancelled) setFarmFpoRelationships([]); });
    return () => { cancelled = true; };
  }, [farmId, user?.role]);

  // Registration queues the same canonical workflow before navigating here.
  // Pick that job up on first load so the page does not require a second manual
  // click to show progress or refresh the intelligence result.
  useEffect(() => {
    let cancelled = false;
    let timer;
    if (manualRunRef.current) return undefined;
    const terminalStatuses = new Set(["completed", "completed_with_warnings", "succeeded", "failed"]);

    async function pollAnalysis() {
      if (manualRunRef.current) return;
      const status = await getLatestAnalysisStatus(farmId).catch(() => null);
      if (cancelled || manualRunRef.current || !status) return;
      setAnalysisStatus(status);

      const progress = analysisProgress(status, pipelineMode === "bootstrap" ? REGISTRATION_PIPELINE_STEPS.length : 0);
      updatePipelineStage(progress.step, progress.label, progress.details);

      if (terminalStatuses.has(status.status)) {
        setRefreshing(false);
        // A saved terminal result must not reopen a modal when the farmer
        // merely views the farm. The loader is reserved for an active job or
        // an analysis explicitly started from this page.
        setPipelineFailure("");
        setPipelineWarning("");
        setPipelineOpen(false);
        await loadLandIntelligence(status).catch(() => null);
        return;
      }

      if (status.status === "running" || status.status === "queued") {
        setRefreshing(true);
        setPipelineOpen(true);
        setPipelineStatus(`Analysis ${status.status}`);
        timer = window.setTimeout(pollAnalysis, 2000);
      }
    }

    pollAnalysis();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [farmId, pipelineMode]);

  useEffect(() => {
    let cancelled = false;
    async function loadDetails() {
      if (!selectedCell?.grid_cell_id) {
        setSelectedDetails(null);
        return;
      }
      const [details, calculations] = await Promise.all([
        getFarmGridCellDetails(farmId, selectedCell.grid_cell_id).catch(() => null),
        getGridCellCalculations(farmId, selectedCell.grid_cell_id).catch(() => []),
      ]);
      if (!cancelled) {
        setSelectedDetails(details ? { ...details, calculated_metrics: calculations } : { calculated_metrics: calculations });
      }
    }
    loadDetails();
    return () => {
      cancelled = true;
    };
  }, [farmId, selectedCell?.grid_cell_id]);

  const farmCalculationList = useMemo(
    () => (Array.isArray(farmCalculations) ? farmCalculations : []),
    [farmCalculations],
  );

  const mergedGridCells = useMemo(() => {
    const valuesById = new Map(
      (Array.isArray(gridValues) ? gridValues : []).map((value) => [String(value.grid_cell_id), value]),
    );
    const calcById = new Map(
      (Array.isArray(gridCalculations) ? gridCalculations : []).map((value) => [String(value.grid_cell_id), value]),
    );
    return gridCells.map((cell) => ({
      ...cell,
      ...(valuesById.get(String(cell.grid_cell_id)) || {}),
      ...(calcById.get(String(cell.grid_cell_id)) || {}),
    }));
  }, [gridCells, gridValues, gridCalculations]);

  // Grid geometry is always shown; calculated scores and raw sensor values are
  // merged in when those endpoints have produced data for the cell.
  const displayCells = mergedGridCells;
  const displaySelected = selectedDetails?.grid_cell || selectedCell || null;
  const h3Enabled = showH3 && canViewTechnicalH3Layer(user);
  const latestSceneDate = farmCalculationList[0]?.result_date || farm?.updated_at;
  const hasAnalysis = Boolean(farmCalculationList.length || gridCalculations.length || gridValues.length);
  const selectedParameterInfo = PARAMETERS.find((item) => item.key === selectedParameter);

  async function runLatestAnalysis() {
    manualRunRef.current = true;
    setPipelineMode("incremental_latest");
    setRefreshing(true);
    setPipelineOpen(true);
    setPipelineFailure("");
    setPipelineWarning("");
    setPipelineDetails([]);
    try {
      updatePipelineStage(0, "Repairing farm metadata", [
        farm?.farm_name ? `Farm: ${farm.farm_name}` : `Farm ID: ${farmId}`,
      ]);

      const payload = {
        analysis_mode: "incremental_latest",
        start_date: (() => {
          const value = new Date();
          value.setDate(value.getDate() - 365);
          return value.toISOString().slice(0, 10);
        })(),
        end_date: new Date().toISOString().slice(0, 10),
        max_cloud_cover: 40,
        provider: "planetary_computer",
        collection_id: "sentinel-2-l2a",
      };

      const queued = await triggerLatestAnalysis(farmId, payload);
      const terminalStatuses = new Set(["completed", "completed_with_warnings", "succeeded", "failed"]);
      let status = queued;
      for (let attempt = 0; attempt < 300; attempt += 1) {
        status = await getLatestAnalysisStatus(farmId);
        setAnalysisStatus(status);
        const progress = analysisProgress(status, 0);
        updatePipelineStage(progress.step, progress.label, progress.details);
        if (terminalStatuses.has(status?.status)) break;
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
      }

      if (status?.status === "failed") {
        setPipelineWarning("");
        setPipelineFailure(status.error_message || "The farm analysis pipeline failed.");
        setPipelineOpen(true);
        setPipelineStatus("Pipeline failed");
      } else if (status?.status === "completed_with_warnings") {
        setPipelineFailure("");
        setPipelineWarning("Analysis completed with source-data warnings. See stage details.");
        setPipelineOpen(true);
        setPipelineStatus("Analysis completed with warnings");
      } else if (status?.status === "completed" || status?.status === "succeeded") {
        setPipelineStatus("Analysis complete");
        setPipelineOpen(false);
      } else {
        setPipelineFailure("Analysis is still running. Reopen this farm to check its status.");
        setPipelineOpen(true);
        setPipelineStatus("Analysis still running");
      }

      try {
        await loadLandIntelligence(status);
      } catch (refreshErr) {
        console.warn("Land intelligence refresh warning", refreshErr);
        setError(refreshErr?.message || "Analysis completed, but the page refresh failed. Please retry.");
      }
    } catch (err) {
      const message = err?.payload?.detail?.message || err?.message || "Analysis failed.";
      setPipelineFailure(message);
      setPipelineWarning("");
      setPipelineOpen(true);
      setPipelineStage(ANALYSIS_STEPS.length - 1);
      setPipelineStatus("Pipeline failed");
    } finally {
      manualRunRef.current = false;
      setRefreshing(false);
    }
  }

  // ---- derived, presentation-only ------------------------------------------
  const locationLine = [farm?.village_name, farm?.block_name, farm?.district_name].filter(Boolean).join(", ") || "Location pending";
  const selectedIndex = displaySelected
    ? displayCells.findIndex((cell) => String(cell.grid_cell_id) === String(displaySelected.grid_cell_id))
    : -1;

  const selectedCalculatedReadings = CALCULATED_METRICS.map((metric) => {
    const detailRow = (selectedDetails?.calculated_metrics || []).find((row) => row.prediction_key === metric.key);
    const gridRow = displaySelected?.calculations?.[metric.key];
    const row = detailRow || gridRow;
    return {
      metric,
      row,
      result: interpretCalculatedMetric(metric.key, row?.score, metricContent),
    };
  });
  const farmCalculatedReadings = CALCULATED_METRICS.map((metric) => {
    const row = farmCalculationList.find((item) => item.prediction_key === metric.key);
    return { metric, row, result: interpretCalculatedMetric(metric.key, row?.score, metricContent) };
  });
  const calculatedReadingsForInterpretation = displaySelected ? selectedCalculatedReadings : farmCalculatedReadings;
  const signalReadings = calculatedReadingsForInterpretation.map(({ metric, result }) => ({ metric, result }));
  const calculatedFieldInterpretationText = buildCalculatedFieldInterpretation(calculatedReadingsForInterpretation, {
    cropName: farm?.crop_name || farm?.crop_code || "Your crop",
    contentOverrides: { fieldInterpretation: metricContent.find((item) => item.metric_key === "crop_condition")?.field_interpretation || {} },
  });
  const calculatedLegend = [
    { label: "Good", color: "#16a34a" },
    { label: "Watch", color: "#84cc16" },
    { label: "Attention", color: "#eab308" },
    { label: "High", color: "#f97316" },
    { label: "Critical", color: "#dc2626" },
  ];

  // Shared body of the selected-cell / farm-summary panel (desktop aside + mobile sheet).
  const panelBody = () => (
    <>
      <div className="text-[10.5px] font-extrabold uppercase tracking-[0.08em] text-[var(--mt-leaf-deep)]">
        {displaySelected ? "Selected land cell" : "Calculated crop intelligence"}
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

      {calculatedReadingsForInterpretation.length > 0 && (
        <div className="mt-4 rounded-[var(--mt-radius-md)] border border-emerald-100 bg-emerald-50/40 p-3">
          <div className="text-[10px] font-extrabold uppercase tracking-[0.08em] text-emerald-800">
            Calculated crop intelligence
          </div>
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {calculatedReadingsForInterpretation.map(({ metric, result }) => (
              <div key={metric.key} className={`rounded-xl border p-2.5 ${result.surfaceClass}`}>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[11px] font-bold leading-tight text-[var(--mt-ink)]">{metricDisplayName(metric, metricContent)}</span>
                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] font-semibold ${result.className}`}>{result.label}</span>
                </div>
                <div className={`mt-1 text-[10px] font-bold ${result.textClass}`}>{result.headline}</div>
                <div className="mt-1 text-[10px] leading-snug text-slate-500">{result.paragraph || result.signalMeaning}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 rounded-[var(--mt-radius-md)] bg-[var(--mt-leaf-tint)] p-4">
        <div className="flex items-center gap-2 text-[12.5px] font-extrabold text-[var(--mt-leaf-deep)]">
          <Sparkles className="h-4 w-4" strokeWidth={2.2} />
          Field interpretation
        </div>
        <p className="mt-1.5 text-[12.5px] font-semibold leading-relaxed text-[var(--mt-ink)]">{calculatedFieldInterpretationText}</p>
      </div>

      {!hasAnalysis && (
        <div className="mt-3 rounded-[12px] bg-[var(--mt-gold-tint)] p-3 text-[12px] font-semibold text-[var(--mt-gold-text)]">
          This field has not been checked yet. Tap &ldquo;Check Again&rdquo; to run the first check.
        </div>
      )}
    </>
  );

  if (loading) {
    return (
      <Motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid min-h-[70vh] place-items-center p-6">
        <div className="w-full max-w-3xl overflow-hidden rounded-[var(--mt-radius-md)] border border-teal-100 bg-gradient-to-r from-teal-50 via-white to-emerald-50 p-5 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="relative grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-teal-700 text-white shadow-lg shadow-teal-700/20">
              <span className="absolute inset-0 animate-ping rounded-2xl bg-teal-400/30" />
              <Sprout className="relative h-6 w-6" strokeWidth={2.1} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="text-sm font-extrabold text-slate-900">Checking your field</p>
                <span className="flex gap-1" aria-hidden="true">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600" />
                </span>
              </div>
              <p className="mt-1 text-xs font-medium text-slate-500">Analysing satellite signals and preparing your field insights.</p>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-teal-100">
                <div className="h-full w-2/5 animate-[pulse_1.8s_ease-in-out_infinite] rounded-full bg-gradient-to-r from-teal-600 via-emerald-500 to-teal-600" />
              </div>
            </div>
          </div>
        </div>
      </Motion.div>
    );
  }

  return (
    <Motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-surface">
      <HexagonPipelineLoader
        open={pipelineOpen}
        title="Land analysis pipeline"
        steps={pipelineSteps}
        currentStep={pipelineStage}
        status={pipelineStatus}
        details={pipelineDetails}
        failure={pipelineFailure}
        warning={pipelineWarning}
        actions={
          pipelineFailure || pipelineWarning
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
        <span className="inline-block max-w-[120px] truncate rounded-full border border-[var(--mt-leaf)]/30 bg-[var(--mt-leaf-tint)] px-2.5 py-1.5 text-[11px] font-extrabold text-[var(--mt-leaf-deep)] sm:max-w-[180px] sm:px-3 sm:text-[12px]">
          {farm?.crop_name || farm?.crop_code || "Crop not configured"}
        </span>
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

      <div className="w-full space-y-4 p-[0.4cm]">

        {loading && (
          <div className="overflow-hidden rounded-[var(--mt-radius-md)] border border-teal-100 bg-gradient-to-r from-teal-50 via-white to-emerald-50 p-5 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="relative grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-teal-700 text-white shadow-lg shadow-teal-700/20">
                <span className="absolute inset-0 animate-ping rounded-2xl bg-teal-400/30" />
                <Sprout className="relative h-6 w-6" strokeWidth={2.1} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-extrabold text-slate-900">Checking your field</p>
                  <span className="flex gap-1" aria-hidden="true">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600 [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-600" />
                  </span>
                </div>
                <p className="mt-1 text-xs font-medium text-slate-500">Analysing satellite signals and preparing your field insights.</p>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-teal-100">
                  <div className="h-full w-2/5 animate-[pulse_1.8s_ease-in-out_infinite] rounded-full bg-gradient-to-r from-teal-600 via-emerald-500 to-teal-600" />
                </div>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-clay)]/30 bg-[var(--mt-clay-tint)] p-4 text-sm font-semibold text-[var(--mt-clay-text)]">
            {error}
          </div>
        )}
        {analysisStatus && ["running", "queued"].includes(analysisStatus.status) && (
          <div className="rounded-[var(--mt-radius-md)] border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-900">
            A new analysis is still running. The values below are from the latest completed analysis and will refresh automatically when this run finishes.
          </div>
        )}

        {/* ── hero ─────────────────────────────────────────────────────── */}
        <div className="grid items-stretch gap-4 overflow-hidden rounded-[var(--mt-radius-lg)] border border-teal-100 bg-white p-4 shadow-sm md:p-5 lg:grid-cols-2">
        <Reveal>
          <section
            className="relative h-full min-h-[280px] overflow-hidden rounded-2xl bg-gradient-to-br from-amber-50 via-white to-teal-50 p-4 md:border-r md:border-teal-100 md:p-5"
          >
            <div className="pointer-events-none absolute -right-12 -top-16 h-44 w-44 rounded-full bg-amber-200/45 blur-2xl" />
            <div className="pointer-events-none absolute -left-16 top-20 h-40 w-40 rounded-full bg-teal-200/35 blur-3xl" />
            <div className="pointer-events-none absolute right-12 top-10 h-2 w-2 rounded-full bg-amber-500/70 shadow-[18px_22px_0_#0f766e,42px_4px_0_#f59e0b,68px_28px_0_#99c97b]" />
            <div className="relative z-10 flex h-full flex-col items-center justify-center text-center">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200/80 bg-white/80 px-3.5 py-1.5 text-[11.5px] font-extrabold tracking-wide text-emerald-900 shadow-sm backdrop-blur-sm">
                <MapPin className="h-3.5 w-3.5" strokeWidth={2.4} />
                Field Check
              </span>
              <h1 className="mt-3 text-[24px] font-extrabold leading-tight tracking-[-0.02em] text-slate-900 md:text-[27px]">{farm?.farm_name || "Your farm"}</h1>
              <div className="mt-2 flex items-center justify-center gap-1.5 text-[13.5px] font-bold text-teal-800">
                <MapPin className="h-3.5 w-3.5 shrink-0" strokeWidth={2.2} />
                <span className="truncate">{locationLine}</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-white/85 px-3.5 py-1.5 text-[12.5px] font-bold text-slate-800 shadow-sm backdrop-blur-sm">
                  <CalendarDays className="h-3.5 w-3.5" strokeWidth={2.2} />
                  {latestSceneDate ? `Checked ${formatDate(latestSceneDate)}` : "Not checked yet"}
                </span>
              </div>
            </div>
            <svg className="pointer-events-none absolute inset-x-0 bottom-0 h-14 w-full opacity-90" viewBox="0 0 1000 70" preserveAspectRatio="none" aria-hidden>
              <path d="M0 70V35 Q150 12 350 30 T700 20 T1000 35V70Z" fill="#C7E5B0" />
              <path d="M0 70V50 Q250 35 500 50 T1000 46V70Z" fill="#9DCE83" />
            </svg>
          </section>
        </Reveal>

        {/* ── priority banner ──────────────────────────────────────────── */}
        {user?.role === "farmer" ? <Reveal delay={0.04} className="h-full"><section className="h-full rounded-2xl bg-gradient-to-br from-teal-50/70 via-white to-emerald-50/40 p-4 md:p-5"><div className="flex h-full flex-col"><div className="flex flex-wrap items-start justify-between gap-4"><div className="flex min-w-0 items-start gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-teal-700 text-white shadow-sm"><Sprout className="h-5 w-5" strokeWidth={2.2} /></span><div className="min-w-0"><p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-teal-700">Farm sharing</p><h2 className="mt-1 text-[17px] font-extrabold leading-tight text-slate-900">FPO connections for this farm</h2><p className="mt-1 max-w-md text-[13px] leading-5 text-slate-600">Connect this farm with trusted support while keeping your other land private.</p></div></div><div className="flex flex-wrap gap-2"><Link to={`/farmer/fpo?farm_id=${encodeURIComponent(farmId)}`} className="inline-flex w-fit items-center justify-center rounded-xl border border-teal-700 bg-teal-700 px-3.5 py-2 text-[13px] font-bold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-teal-800 hover:shadow-md">Manage FPOs</Link><Link to={`/farmer/fpo?farm_id=${encodeURIComponent(farmId)}`} className="inline-flex w-fit items-center justify-center rounded-xl border border-teal-200 bg-white px-3.5 py-2 text-[13px] font-bold text-teal-800 shadow-sm transition hover:-translate-y-0.5 hover:border-teal-300 hover:bg-teal-50 hover:shadow-md">Connect FPO</Link></div></div><div className="mt-5 border-t border-teal-200/70 pt-4">{farmFpoRelationships.length ? <div className="flex flex-wrap gap-2">{farmFpoRelationships.map((relationship) => <Link key={relationship.relationship_id} to={`/farmer/farms/${farmId}/fpo/${relationship.relationship_id}`} className="inline-flex items-center gap-2 rounded-xl border border-teal-100 bg-white/85 px-3 py-2 text-sm font-bold text-slate-800 shadow-sm transition hover:border-teal-300 hover:bg-white"><span>{relationship.fpo_name || "FPO"}</span><span className={`rounded-full px-2 py-0.5 text-[10px] font-black uppercase ${relationship.status === "ACTIVE" ? "bg-emerald-100 text-emerald-800" : relationship.status === "PENDING_FPO_ACCEPTANCE" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"}`}>{String(relationship.status || "").replaceAll("_", " ")}</span></Link>)}</div> : <div className="flex items-start gap-3 rounded-xl border border-dashed border-teal-200 bg-white/70 px-3.5 py-3"><span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-teal-100 text-teal-700"><Sparkles className="h-3.5 w-3.5" /></span><div><p className="text-[13px] font-bold text-slate-800">No FPO connected yet</p><p className="mt-0.5 text-[12px] leading-5 text-slate-600">Find an approved FPO to send a consent-based request for this farm.</p></div></div>}</div></div></section></Reveal> : null}
        </div>

        {/* ── crop-specific calculated intelligence ────────────────────── */}
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
                h3Cells={h3Enabled ? h3Cells : []}
                selectedParameter={selectedParameter}
                onGridCellClick={setSelectedCell}
                selectedGridCellId={displaySelected?.grid_cell_id}
                showH3Layer={h3Enabled}
                userRole={user?.role}
              />
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-[var(--mt-line)] px-4 py-3.5 md:px-5">
              {calculatedLegend.map((status) => (
                <span key={status.label} className="flex items-center gap-1.5 text-[12px] font-bold text-[var(--mt-ink)]">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: status.color }} />
                  {status.label}
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
        {calculatedReadingsForInterpretation.length > 0 && (
          <div className="mb-3 overflow-hidden rounded-[var(--mt-radius-md)] border border-emerald-100 bg-white">
            {signalReadings.map(({ metric, result }) => {
              const Icon = CALCULATED_METRIC_ICONS[metric.key] || Activity;
              return (
                <div key={metric.key} className="flex flex-col gap-3 border-b border-[var(--mt-line)] p-4 last:border-b-0 md:flex-row md:items-start md:gap-5 md:px-5" style={{ borderLeft: `4px solid ${result.color}` }}>
                  <div className="flex items-center gap-3 md:w-[240px] md:shrink-0">
                    <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-[11px] ${result.className}`}><Icon className="h-4 w-4" style={{ color: result.color }} strokeWidth={2.2} /></span>
                    <div className="min-w-0"><div className="text-[14px] font-extrabold text-[var(--mt-ink)]">{metricDisplayName(metric, metricContent)}</div><StatusBadge result={result} className="mt-1" /></div>
                  </div>
                  <div className="text-[13.5px] font-semibold leading-relaxed text-[var(--mt-ink)]">
                    <p>{result.signalMeaning}</p>
                    <p className="mt-1 text-[12px] font-bold" style={{ color: result.color }}>{result.headline || result.paragraph}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Motion.div>
  );
}
