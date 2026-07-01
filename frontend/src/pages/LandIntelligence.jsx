import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Cloud, Hexagon, Leaf, RefreshCw, Thermometer, Waves, Mountain, Droplets } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import StatStrip from "@/components/ui-custom/StatStrip";
import LandGridMap from "@/components/ui-custom/LandGridMap";
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
import { materializeFarmAnalysis, materializeFarmGrid, materializeFarmTrends } from "@/lib/api/hotStream";
import { canViewTechnicalH3Layer } from "@/lib/rbac/permissions";
import { getStoredUser } from "@/lib/auth/session";

const PARAMETERS = [
  { key: "ndvi", label: "NDVI" },
  { key: "evi", label: "EVI" },
  { key: "savi", label: "SAVI" },
  { key: "ndre", label: "NDRE" },
  { key: "ndmi", label: "NDMI" },
  { key: "ndwi", label: "NDWI" },
  { key: "msi", label: "MSI" },
  { key: "bsi", label: "BSI" },
  { key: "temperature", label: "Surface Temp" },
  { key: "cloud", label: "Cloud" },
  { key: "valid_pixels", label: "Valid Pixels" },
];

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.items || payload?.data || payload?.grid_cells || payload?.grid_values || payload?.h3_cells || [];
}

function pretty(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "—";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toFixed(digits);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function pickTrend(summary, trends, key) {
  return trends?.[0]?.[key] || summary?.[key] || "stable";
}

function valueFor(cell, param) {
  const fallback = (a, b, c) => a ?? b ?? c ?? null;
  switch (param) {
    case "ndvi": return fallback(cell.ndvi, cell.weighted_ndvi);
    case "evi": return fallback(cell.evi, cell.weighted_evi);
    case "savi": return fallback(cell.savi, cell.weighted_savi);
    case "ndre": return fallback(cell.ndre, cell.weighted_ndre);
    case "ndmi": return fallback(cell.ndmi, cell.weighted_ndmi);
    case "ndwi": return fallback(cell.ndwi, cell.weighted_ndwi);
    case "msi": return fallback(cell.msi, cell.weighted_msi);
    case "bsi": return fallback(cell.bsi, cell.weighted_bsi);
    case "temperature": return fallback(cell.surface_temp_c, cell.weighted_surface_temp_c);
    case "cloud": return fallback(cell.cloud_percentage, cell.avg_cloud_percentage);
    case "valid_pixels": return fallback(cell.valid_pixel_percentage);
    default: return null;
  }
}

function tone(value, param) {
  const num = Number(value);
  if (Number.isNaN(num)) return "text-gray-500";
  if (param === "cloud") return num > 40 ? "text-slate-500" : "text-emerald-700";
  if (param === "temperature") return num > 35 ? "text-rose-600" : "text-amber-700";
  if (param === "bsi") return num > 0.15 ? "text-amber-700" : "text-emerald-700";
  return num >= 0.45 ? "text-emerald-700" : num >= 0.25 ? "text-lime-700" : "text-amber-700";
}

function recommendationFor(cell = {}) {
  const notes = [];
  if (Number(cell.ndvi ?? cell.weighted_ndvi ?? 0) < 0.25) notes.push("Vegetation stress detected");
  if (Number(cell.ndmi ?? cell.weighted_ndmi ?? 0) < 0.05 || Number(cell.ndwi ?? cell.weighted_ndwi ?? 0) < 0.05) notes.push("Moisture stress possible");
  if (Number(cell.bsi ?? cell.weighted_bsi ?? 0) > 0.15) notes.push("Bare soil exposure is high");
  if (Number(cell.cloud_percentage ?? cell.avg_cloud_percentage ?? 0) > 40) notes.push("Satellite data quality reduced by cloud");
  return notes.length ? notes.join(". ") : "Conditions look stable";
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
  const [history, setHistory] = useState([]);
  const [trends, setTrends] = useState([]);
  const [gridCells, setGridCells] = useState([]);
  const [gridValues, setGridValues] = useState([]);
  const [h3Cells, setH3Cells] = useState([]);
  const [selectedParameter, setSelectedParameter] = useState("ndvi");
  const [selectedCell, setSelectedCell] = useState(null);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [hoveredCell, setHoveredCell] = useState(null);
  const [showH3, setShowH3] = useState(false);

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
    return () => { cancelled = true; };
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
    return () => { cancelled = true; };
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
  const stats = [
    { label: "Farm area", value: farm?.area_acres ? pretty(farm.area_acres, 2) : "—", unit: "ac" },
    { label: "Grid cells", value: displayCells.length || "—", unit: "" },
    { label: "H3 cells", value: summary?.total_farm_h3_cells ?? farm?.h3_cell_count ?? h3Cells.length ?? "—", unit: "" },
    { label: "Latest scene", value: formatDate(latestSentinel?.scene_datetime || latestSentinel?.observation_date || latestSummary.latest_snapshot_date), unit: "" },
    { label: "Cloud cover", value: latestSentinel?.cloud_percentage ?? latestSummary.avg_cloud_percentage ?? "—", unit: "%" },
    { label: "Valid pixels", value: latestSummary.valid_pixel_percentage ?? latestSentinel?.valid_pixels_pct ?? "—", unit: "%" },
  ];

  async function runLatestAnalysis() {
    setRefreshing(true);
    try {
      await materializeFarmAnalysis(farmId, {
        start_date: "2025-12-01",
        end_date: "2025-12-31",
        max_cloud_cover: 30,
        h3_resolution: 12,
        provider: "planetary_computer",
        collection_id: "sentinel-2-l2a",
        use_tiny_preview_bbox: true,
        tiny_bbox_size_deg: 0.0002,
      }).catch(() => null);
      await materializeFarmTrends(farmId, {}).catch(() => null);
      await materializeFarmGrid(farmId, {}).catch(() => null);
      await loadLandIntelligence();
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mx-auto max-w-[1600px] space-y-5 p-4 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-emerald-600">Land Intelligence</p>
          <h1 className="mt-1 text-2xl font-black text-gray-900">{farm?.farm_name || "Farm"} {farm?.survey_number ? `· ${farm.survey_number}` : ""}</h1>
          <p className="text-sm text-gray-500">{farm?.village_name || "Village"}, {farm?.block_name || "Block"}, {farm?.district_name || "District"}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-gray-500">
            <span className="rounded-full bg-gray-100 px-3 py-1 font-semibold text-gray-600">Scene date: {formatDate(latestSentinel?.scene_datetime || latestSentinel?.observation_date || latestSummary.latest_snapshot_date)}</span>
            <span className="rounded-full bg-gray-100 px-3 py-1 font-semibold text-gray-600">Scene ID: {latestSentinel?.scene_id || latestSummary.latest_scene_id || "—"}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {canViewTechnicalH3Layer(user) && (
            <Button variant="outline" className="rounded-xl" onClick={() => setShowH3((v) => !v)}>
              <Hexagon className="mr-1 h-4 w-4" />
              {showH3 ? "Hide H3" : "Show H3"}
            </Button>
          )}
          <Button onClick={runLatestAnalysis} disabled={refreshing} className="rounded-xl bg-emerald-600 text-white">
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Run Latest Analysis
          </Button>
        </div>
      </div>

      {loading && <div className="rounded-3xl border border-gray-200 bg-white p-6 text-sm text-gray-500 shadow-sm">Loading land intelligence...</div>}
      {error && <div className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}

      <StatStrip items={stats.map((item) => ({ ...item, icon: item.label === "Cloud cover" ? Cloud : item.label === "Valid pixels" ? Waves : item.label === "Farm area" ? Mountain : item.label === "H3 cells" ? Hexagon : item.label === "Latest scene" ? RefreshCw : item.label === "Farm area" ? Mountain : Leaf }))} />

      <PipelineStepper steps={["Location", "Farmer", "Boundary", "Grid", "Satellite", "Raster", "Intelligence"]} currentStep={7} />

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-4">
          <div className="rounded-3xl border border-gray-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-4 py-3">
              <div className="flex flex-wrap gap-2">
                {PARAMETERS.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setSelectedParameter(item.key)}
                    className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition ${selectedParameter === item.key ? "bg-emerald-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="rounded-full bg-emerald-50 px-3 py-1 font-semibold text-emerald-700">Visual grid default</span>
                <span className={`rounded-full px-3 py-1 font-semibold ${h3Enabled ? "bg-violet-50 text-violet-700" : "bg-gray-100 text-gray-500"}`}>
                  {h3Enabled ? "H3 technical layer on" : "H3 technical layer off"}
                </span>
              </div>
            </div>
            <div className="p-4">
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
                onGridCellHover={setSelectedCell}
              />
            </div>
          </div>

          <div className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-200 px-4 py-3">
              <p className="text-sm font-bold text-gray-900">Grid Cells</p>
              <p className="text-xs text-gray-500">{displayCells.length || 0} cells</p>
            </div>
            <div className="max-h-80 overflow-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-gray-50">
                  <tr className="text-gray-500">
                    <th className="px-3 py-2">Cell</th>
                    <th className="px-3 py-2">NDVI</th>
                    <th className="px-3 py-2">NDMI</th>
                    <th className="px-3 py-2">BSI</th>
                    <th className="px-3 py-2">Temp</th>
                    <th className="px-3 py-2">Cloud</th>
                  </tr>
                </thead>
                <tbody>
                  {displayCells.map((cell, index) => (
                    <tr key={cell.grid_cell_id || index} onClick={() => setSelectedCell(cell)} className={`cursor-pointer border-t border-gray-100 hover:bg-emerald-50 ${displaySelected?.grid_cell_id === cell.grid_cell_id ? "bg-emerald-50" : ""}`}>
                      <td className="px-3 py-2 font-semibold">{String(index + 1).padStart(2, "0")}</td>
                      <td className="px-3 py-2">{pretty(valueFor(cell, "ndvi"), 3)}</td>
                      <td className="px-3 py-2">{pretty(valueFor(cell, "ndmi"), 3)}</td>
                      <td className="px-3 py-2">{pretty(valueFor(cell, "bsi"), 3)}</td>
                      <td className="px-3 py-2">{pretty(valueFor(cell, "temperature"), 1)}</td>
                      <td className="px-3 py-2">{pretty(valueFor(cell, "cloud"), 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-3xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-gray-400">{displaySelected ? "Grid cell details" : "Farm summary"}</p>
            {displaySelected ? (
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-400">Cell ID</span><span className="font-mono text-[11px]">{displaySelected.grid_cell_id}</span></div>
                <div className="flex justify-between"><span className="text-gray-400">Row / Col</span><span>{displaySelected.grid_row ?? "—"} / {displaySelected.grid_col ?? "—"}</span></div>
                <div className="flex justify-between"><span className="text-gray-400">Coverage</span><span>{pretty(selectedDetails?.grid_cell?.coverage_ratio ?? displaySelected.coverage_ratio, 2)}</span></div>
                <div className="grid grid-cols-2 gap-2 pt-2">
                  {[
                    ["NDVI", selectedDetails?.weighted_average?.ndvi ?? displaySelected.ndvi],
                    ["NDMI", selectedDetails?.weighted_average?.ndmi ?? displaySelected.ndmi],
                    ["NDWI", selectedDetails?.weighted_average?.ndwi ?? displaySelected.ndwi],
                    ["EVI", selectedDetails?.weighted_average?.evi ?? displaySelected.evi],
                    ["SAVI", selectedDetails?.weighted_average?.savi ?? displaySelected.savi],
                    ["MSI", selectedDetails?.weighted_average?.msi ?? displaySelected.msi],
                    ["NBR", selectedDetails?.weighted_average?.nbr ?? displaySelected.nbr],
                    ["NDRE", selectedDetails?.weighted_average?.ndre ?? displaySelected.ndre],
                    ["BSI", selectedDetails?.weighted_average?.bsi ?? displaySelected.bsi],
                    ["Temp", selectedDetails?.weighted_average?.surface_temp_c ?? displaySelected.surface_temp_c],
                    ["Cloud", selectedDetails?.weighted_average?.cloud_percentage ?? displaySelected.cloud_percentage],
                    ["Valid", selectedDetails?.weighted_average?.valid_pixel_percentage ?? displaySelected.valid_pixel_percentage],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-gray-100 bg-gray-50 p-2">
                      <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400">{label}</div>
                      <div className={`text-sm font-semibold ${tone(value, label.toLowerCase())}`}>{pretty(value, 3)}</div>
                    </div>
                  ))}
                </div>
                <div className="rounded-2xl bg-gray-50 p-3 text-xs text-gray-600">{recommendationFor(selectedDetails?.latest_values || displaySelected)}</div>
                <div className="rounded-2xl border border-gray-100 bg-white p-3">
                  <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-gray-400">H3 contributions</div>
                  <div className="space-y-2">
                    {(selectedDetails?.h3_contributions || []).slice(0, 6).map((row) => (
                      <div key={row.h3_index} className="rounded-xl border border-gray-100 p-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono">{String(row.h3_index)}</span>
                          <span className="font-semibold">{row.overlap_percentage}%</span>
                        </div>
                        <div className="mt-1 text-gray-500">NDVI {pretty(row.ndvi, 3)} · NDMI {pretty(row.ndmi, 3)} · BSI {pretty(row.bsi, 3)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div><span className="block text-gray-400">Weighted NDVI</span><span className={`font-semibold ${tone(latestSummary.weighted_ndvi ?? latestSummary.avg_ndvi, "ndvi")}`}>{pretty(latestSummary.weighted_ndvi ?? latestSummary.avg_ndvi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted NDMI</span><span className={`font-semibold ${tone(latestSummary.weighted_ndmi ?? latestSummary.avg_ndmi, "ndmi")}`}>{pretty(latestSummary.weighted_ndmi ?? latestSummary.avg_ndmi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted NDWI</span><span className="font-semibold">{pretty(latestSummary.weighted_ndwi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted BSI</span><span className={`font-semibold ${tone(latestSummary.weighted_bsi ?? latestSummary.avg_bsi, "bsi")}`}>{pretty(latestSummary.weighted_bsi ?? latestSummary.avg_bsi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted EVI</span><span className="font-semibold">{pretty(latestSummary.weighted_evi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted SAVI</span><span className="font-semibold">{pretty(latestSummary.weighted_savi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted MSI</span><span className="font-semibold">{pretty(latestSummary.weighted_msi, 3)}</span></div>
                <div><span className="block text-gray-400">Weighted NDRE</span><span className="font-semibold">{pretty(latestSummary.weighted_ndre, 3)}</span></div>
                <div><span className="block text-gray-400">Cloud</span><span className="font-semibold">{pretty(latestSummary.avg_cloud_percentage, 0)}</span></div>
                <div><span className="block text-gray-400">Valid pixels</span><span className="font-semibold">{pretty(latestSummary.valid_pixel_percentage, 0)}</span></div>
                <div><span className="block text-gray-400">Farm H3 cells</span><span className="font-semibold">{latestSummary.total_farm_h3_cells ?? latestSummary.total_h3_cells ?? h3Cells.length ?? "—"}</span></div>
                <div><span className="block text-gray-400">Processed H3 cells</span><span className="font-semibold">{latestSummary.processed_h3_cells ?? latestSummary.latest_processed_h3_cells ?? "—"}</span></div>
                <div><span className="block text-gray-400">Grid cells</span><span className="font-semibold">{latestSummary.total_grid_cells ?? displayCells.length ?? "—"}</span></div>
                <div><span className="block text-gray-400">Grid cells with values</span><span className="font-semibold">{latestSummary.grid_cells_with_values ?? displayCells.length ?? "—"}</span></div>
                <div className="col-span-2 rounded-2xl bg-gray-50 p-3 text-xs text-gray-600">Vegetation: {pickTrend(latestSummary, trends, "vegetation_trend")} · Moisture: {pickTrend(latestSummary, trends, "moisture_trend")} · Soil: {pickTrend(latestSummary, trends, "soil_exposure_trend")}</div>
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-gray-400">Trend summary</p>
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">Vegetation</span><span className="font-semibold">{pickTrend(latestSummary, trends, "vegetation_trend")}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Moisture</span><span className="font-semibold">{pickTrend(latestSummary, trends, "moisture_trend")}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Soil</span><span className="font-semibold">{pickTrend(latestSummary, trends, "soil_exposure_trend")}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">History points</span><span className="font-semibold">{history.length || "—"}</span></div>
            </div>
            <div className="mt-4 text-xs text-gray-500">
              {canViewTechnicalH3Layer(user) ? "H3 technical layer available through the toggle." : "Farmer view defaults to the square visual grid."}
            </div>
            <div className="mt-3">
              <Link to={`/farmers/${farm?.farmer_id || ""}`} className="text-xs font-semibold text-emerald-700 hover:underline">Open farmer profile</Link>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
