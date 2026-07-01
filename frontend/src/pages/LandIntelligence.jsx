import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  MapPin, Hexagon, User, Satellite, Leaf, Droplets,
  Mountain, Cloud, Layers, RefreshCw, Thermometer, Sun, Check,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import IndexReadout from "@/components/ui-custom/IndexReadout";
import { getFarm } from "@/lib/api/farm";
import {
  getFarmGridCells,
  getFarmH3Cells,
  getFarmSummary,
  getFarmTrends,
  getLatestGridValues,
  getLatestSentinel2,
  getSentinel2History,
} from "@/lib/api/analytics";
import {
  materializeFarmAnalysis,
  materializeFarmGrid,
  materializeFarmTrends,
} from "@/lib/api/hotStream";
import { canViewTechnicalH3Layer } from "@/lib/rbac/permissions";
import { getStoredUser } from "@/lib/auth/session";

function HexGrid({ cells, hoveredCell, setHoveredCell, selectedCell, setSelectedCell }) {
  const cols = 6;
  return (
    <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {cells.map((cell, index) => {
        const normalized = Math.max(0, Math.min(1, Number(cell.ndvi || cell.avg_ndvi || 0)));
        const green = Math.floor(normalized * 255);
        const bg = `rgb(${255 - green}, ${100 + green * 0.6}, 80)`;
        const isHovered = hoveredCell === index;
        const isSelected = selectedCell === index;
        return (
          <motion.div
            key={cell.id || index}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.02 }}
            onMouseEnter={() => setHoveredCell(index)}
            onMouseLeave={() => setHoveredCell(null)}
            onClick={() => setSelectedCell(isSelected ? null : index)}
            className={`relative aspect-square cursor-pointer rounded-sm transition-all ${
              isSelected ? "ring-2 ring-foreground ring-offset-1" :
              isHovered ? "ring-1 ring-primary ring-offset-1" : ""
            }`}
            style={{ backgroundColor: bg }}
          >
            {!cell.cloudFree && <Cloud className="absolute right-0.5 top-0.5 h-2.5 w-2.5 text-white/70" />}
            {isHovered && (
              <div className="absolute bottom-full left-1/2 z-20 mb-2 w-40 -translate-x-1/2 rounded-sm border border-border bg-card p-2 shadow-lg">
                <div className="space-y-1 text-[9px]">
                  <div className="flex justify-between"><span className="text-muted-foreground">Cell</span><span className="font-mono">{index + 1}/{cells.length}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">NDVI</span><span className="font-display font-bold text-primary">{Number(cell.ndvi || cell.avg_ndvi || 0).toFixed(3)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Moisture</span><span className="font-display font-bold text-blue-600">{Number(cell.moisture || cell.ndmi || cell.avg_ndmi || 0).toFixed(3)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Bare Soil</span><span className="font-display font-bold">{(Number(cell.bareSoil || cell.bsi || 0) * 100).toFixed(1)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Valid Px</span><span>{Math.round(Number(cell.validPixels || cell.valid_pixels_pct || 0))}%</span></div>
                </div>
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

export default function LandIntelligence() {
  const { farmId } = useParams();
  const user = getStoredUser();
  const [hoveredCell, setHoveredCell] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);
  const [viewMode, setViewMode] = useState(canViewTechnicalH3Layer(user) ? "h3" : "grid");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [farm, setFarm] = useState(null);
  const [summary, setSummary] = useState(null);
  const [latestScene, setLatestScene] = useState(null);
  const [history, setHistory] = useState([]);
  const [trends, setTrends] = useState(null);
  const [gridCells, setGridCells] = useState([]);
  const [gridValues, setGridValues] = useState([]);
  const [h3Cells, setH3Cells] = useState([]);

  async function loadData() {
    setError("");
    try {
      const [
        farmPayload,
        summaryPayload,
        latestScenePayload,
        historyPayload,
        trendsPayload,
        gridCellsPayload,
        gridValuesPayload,
        h3CellsPayload,
      ] = await Promise.all([
        getFarm(farmId),
        getFarmSummary(farmId).catch(() => null),
        getLatestSentinel2(farmId).catch(() => null),
        getSentinel2History(farmId, 10).catch(() => []),
        getFarmTrends(farmId).catch(() => null),
        getFarmGridCells(farmId).catch(() => []),
        getLatestGridValues(farmId).catch(() => []),
        getFarmH3Cells(farmId).catch(() => []),
      ]);

      setFarm(farmPayload);
      setSummary(summaryPayload);
      setLatestScene(latestScenePayload);
      setHistory(Array.isArray(historyPayload) ? historyPayload : []);
      setTrends(trendsPayload);
      setGridCells(Array.isArray(gridCellsPayload) ? gridCellsPayload : []);
      setGridValues(Array.isArray(gridValuesPayload) ? gridValuesPayload : []);
      setH3Cells(Array.isArray(h3CellsPayload) ? h3CellsPayload : []);
    } catch (err) {
      setError(typeof err?.message === "string" ? err.message : "Unable to load land intelligence.");
    }
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loadData().finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [farmId]);

  const displayCells = useMemo(() => {
    const source = viewMode === "grid" && gridValues.length ? gridValues : h3Cells;
    return source.map((item, index) => ({
      id: item.grid_cell_id || item.h3_index || index,
      ndvi: item.ndvi,
      moisture: item.ndmi || item.ndwi,
      bareSoil: item.bsi,
      heat: item.temperature_c || 30,
      validPixels: item.valid_pixels_pct || latestScene?.valid_pixels_pct || 0,
      cloudFree: Number(latestScene?.cloud_percentage || 0) < 40,
    }));
  }, [gridValues, h3Cells, latestScene, viewMode]);

  const activeCell = selectedCell !== null ? displayCells[selectedCell] : null;
  const avgNdvi = Number(summary?.avg_ndvi ?? latestScene?.ndvi ?? 0);
  const avgMoisture = Number(summary?.avg_ndmi ?? latestScene?.ndmi ?? 0);
  const avgBareSoil = Number(summary?.avg_bsi ?? latestScene?.bsi ?? 0);
  const avgHeat = Number(summary?.avg_temperature_c ?? 30);
  const cloudFreeCount = displayCells.filter((cell) => cell.cloudFree).length;
  const avgValidPixels = displayCells.length
    ? Math.round(displayCells.reduce((sum, cell) => sum + Number(cell.validPixels || 0), 0) / displayCells.length)
    : Math.round(Number(latestScene?.valid_pixels_pct || 0));
  const vegetationTrend = trends?.vegetation_trend || "pending";
  const moistureTrend = trends?.moisture_trend || "pending";
  const soilTrend = trends?.soil_exposure_trend || "pending";
  const sceneQuality = Number(latestScene?.cloud_percentage || 0) <= 20 ? "clear" : Number(latestScene?.cloud_percentage || 0) <= 40 ? "usable" : "cloudy";
  const satelliteStats = [
    { label: "Vegetation health", value: avgNdvi, unit: "NDVI", tone: "bg-primary" },
    { label: "Moisture health", value: avgMoisture, unit: "NDMI", tone: "bg-blue-500" },
    { label: "Bare soil exposure", value: avgBareSoil, unit: "BSI", tone: "bg-amber-600" },
    { label: "Surface warmth", value: avgHeat, unit: "°C", tone: "bg-red-500" },
    { label: "Cloud cover", value: Number(latestScene?.cloud_percentage || 0), unit: "%", tone: "bg-slate-500" },
    { label: "Valid pixels", value: avgValidPixels, unit: "%", tone: "bg-emerald-500" },
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
      await loadData();
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-4 p-4 md:p-6">
      {loading && (
        <div className="rounded-sm border border-border bg-card p-4 text-sm text-muted-foreground">
          Loading land intelligence...
        </div>
      )}

      {!loading && error && (
        <div className="rounded-sm border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
          {error}
        </div>
      )}

      <div className="rounded-sm border border-border bg-card p-3">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-display uppercase tracking-widest text-muted-foreground">Farm</span>
            <span className="font-display font-bold text-foreground">{farm?.farm_id || farmId}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <User className="h-3 w-3 text-muted-foreground" />
            <Link to={farm?.farmer_id ? `/farmers/${farm.farmer_id}` : "#"} className="transition-colors hover:text-primary">
              {summary?.farmer_name || "Farmer profile"}
            </Link>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3 w-3 text-muted-foreground" />
            <span>{farm?.village_name || "Village"}, {farm?.block_name || "Block"}, {farm?.district_name || "District"}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Hexagon className="h-3 w-3 text-muted-foreground" />
            <span>{Number(farm?.area_acres || 0).toFixed(1)} ac · {farm?.h3_cell_count || h3Cells.length} cells · Res {farm?.h3_resolution || 12}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Satellite className="h-3 w-3 text-muted-foreground" />
            <span>{latestScene?.observation_date || "No scene"} · {Number(latestScene?.cloud_percentage || 0).toFixed(1)}% cloud</span>
          </div>
          <VerificationStamp label={farm?.is_active ? "VERIFIED" : "PENDING"} type={farm?.is_active ? "success" : "pending"} compact />
        </div>
      </div>

      <PipelineStepper
        steps={["Location", "Farmer", "Boundary", "H3 Grid", "Satellite", "Raster", "Intelligence"]}
        currentStep={farm ? 7 : 4}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="overflow-hidden rounded-sm border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <div className="flex items-center gap-3">
                <span className="text-xs font-display font-bold uppercase tracking-wider text-foreground">Land View</span>
                <div className="flex items-center gap-1 rounded-sm bg-muted p-0.5">
                  {canViewTechnicalH3Layer(user) && (
                    <button
                      onClick={() => setViewMode("h3")}
                      className={`rounded-sm px-2 py-1 text-[10px] font-display uppercase tracking-wider transition-colors ${viewMode === "h3" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"}`}
                    >
                      <Hexagon className="mr-1 inline h-3 w-3" />
                      H3 Grid
                    </button>
                  )}
                  <button
                    onClick={() => setViewMode("grid")}
                    className={`rounded-sm px-2 py-1 text-[10px] font-display uppercase tracking-wider transition-colors ${viewMode === "grid" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"}`}
                  >
                    <Layers className="mr-1 inline h-3 w-3" />
                    Visual Grid
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={runLatestAnalysis} disabled={refreshing} className="h-7 rounded-sm text-[10px] font-display uppercase tracking-wider">
                  <RefreshCw className={`mr-1 h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                  Run Latest Analysis
                </Button>
              </div>
            </div>

            <div className="topo-texture bg-muted/30 p-4">
              {displayCells.length ? (
                <div className="mx-auto max-w-md">
                  <HexGrid
                    cells={displayCells}
                    hoveredCell={hoveredCell}
                    setHoveredCell={setHoveredCell}
                    selectedCell={selectedCell}
                    setSelectedCell={setSelectedCell}
                  />
                  <div className="mt-3 flex items-center justify-center gap-2">
                    <span className="text-[8px] font-display uppercase tracking-wider text-muted-foreground">Low health</span>
                    <div className="flex gap-0.5">
                      {[0.2, 0.35, 0.5, 0.65, 0.8].map((value) => (
                        <div key={value} className="h-2 w-5 rounded-sm" style={{ backgroundColor: `rgb(${255 - value * 255}, ${100 + value * 153}, 80)` }} />
                      ))}
                    </div>
                    <span className="text-[8px] font-display uppercase tracking-wider text-muted-foreground">High health</span>
                  </div>
                </div>
              ) : (
                <div className="flex h-64 items-center justify-center">
                  <div className="text-center">
                    <Layers className="mx-auto mb-2 h-8 w-8 text-muted-foreground/40" />
                    <p className="text-xs text-muted-foreground">Grid values are not available yet for this farm.</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {activeCell && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="overflow-hidden rounded-sm border border-primary/30 bg-card">
              <div className="flex items-center justify-between border-b border-border bg-primary/5 px-4 py-2.5">
                <span className="text-xs font-display font-bold uppercase tracking-wider text-primary">Cell {selectedCell + 1} - Detailed Analysis</span>
                <button onClick={() => setSelectedCell(null)} className="text-[10px] text-muted-foreground hover:text-foreground">Close</button>
              </div>
              <div className="grid grid-cols-2 gap-4 p-4 md:grid-cols-4">
                <IndexReadout label="Vegetation" value={Number(activeCell.ndvi || 0)} icon={<Leaf />} color="bg-primary" />
                <IndexReadout label="Moisture" value={Number(activeCell.moisture || 0)} icon={<Droplets />} color="bg-blue-500" />
                <IndexReadout label="Bare Soil" value={Number(activeCell.bareSoil || 0)} icon={<Mountain />} color="bg-amber-600" />
                <IndexReadout label="Surface Temp" value={Number(activeCell.heat || 30)} unit="°C" min={25} max={40} icon={<Thermometer />} color="bg-red-500" />
              </div>
              <div className="flex items-center gap-4 px-4 pb-3 text-[9px] font-display uppercase tracking-wider text-muted-foreground">
                <span>Valid pixels: {Math.round(Number(activeCell.validPixels || 0))}%</span>
                <span>Cloud-free: {activeCell.cloudFree ? "Yes" : "No"}</span>
                <span>Cell source: {viewMode.toUpperCase()}</span>
              </div>
            </motion.div>
          )}

          <div className="overflow-hidden rounded-sm border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <span className="text-xs font-display font-bold uppercase tracking-wider text-foreground">
                {viewMode === "grid" ? "Grid Cell Feature Table" : "H3 Cell Feature Table"}
              </span>
              <span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">{displayCells.length} cells</span>
            </div>
            <div className="scrollbar-hide max-h-64 overflow-x-auto overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm">
                  <tr className="border-b border-border">
                    {["Cell", "NDVI", "Moisture", "Bare Soil", "Temp °C", "Valid Px %", "Cloud"].map((header) => (
                      <th key={header} className="px-3 py-2 text-left text-[9px] font-display font-semibold uppercase tracking-wider text-muted-foreground">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {displayCells.map((cell, index) => (
                    <tr
                      key={cell.id || index}
                      onClick={() => setSelectedCell(index)}
                      className={`cursor-pointer border-b border-border transition-colors last:border-0 ${selectedCell === index ? "bg-primary/5" : "hover:bg-muted/30"}`}
                    >
                      <td className="px-3 py-1.5 font-display font-bold">{String(index + 1).padStart(2, "0")}</td>
                      <td className="px-3 py-1.5 font-display font-bold text-primary">{Number(cell.ndvi || 0).toFixed(3)}</td>
                      <td className="px-3 py-1.5 font-display font-bold text-blue-600">{Number(cell.moisture || 0).toFixed(3)}</td>
                      <td className="px-3 py-1.5">{(Number(cell.bareSoil || 0) * 100).toFixed(1)}%</td>
                      <td className="px-3 py-1.5">{Number(cell.heat || 30).toFixed(1)}</td>
                      <td className="px-3 py-1.5">{Math.round(Number(cell.validPixels || 0))}</td>
                      <td className="px-3 py-1.5">{cell.cloudFree ? <Check className="h-3 w-3 text-primary" /> : <Cloud className="h-3 w-3 text-muted-foreground" />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-4 rounded-sm border border-border bg-card p-4">
            <span className="block text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground">Farm-Level Indices</span>
            <div className="grid grid-cols-2 gap-3">
              {satelliteStats.map((stat) => (
                <div key={stat.label} className="rounded-sm border border-border bg-background p-3">
                  <p className="text-[9px] font-display uppercase tracking-widest text-muted-foreground">{stat.label}</p>
                  <div className="mt-1 flex items-end justify-between gap-2">
                    <span className="text-lg font-display font-bold text-foreground">
                      {typeof stat.value === "number" ? stat.value.toFixed(stat.unit === "%" ? 0 : 2) : stat.value}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-[9px] font-semibold text-white ${stat.tone}`}>{stat.unit}</span>
                  </div>
                </div>
              ))}
            </div>
            <IndexReadout label="Vegetation (NDVI)" value={avgNdvi} icon={<Leaf />} color="bg-primary" />
            <IndexReadout label="Moisture (NDMI)" value={avgMoisture} icon={<Droplets />} color="bg-blue-500" />
            <IndexReadout label="Bare Soil Index" value={avgBareSoil} icon={<Mountain />} color="bg-amber-600" />
            <IndexReadout label="Avg. Surface Temp" value={avgHeat} unit="°C" min={25} max={40} icon={<Thermometer />} color="bg-red-500" />
          </div>

          <div className="space-y-3 rounded-sm border border-border bg-card p-4">
            <span className="block text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground">Satellite Scene</span>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">Scene ID</span><span className="font-mono text-[9px]">{latestScene?.scene_id ? `...${latestScene.scene_id.slice(-16)}` : "Pending"}</span></div>
              <div className="flex justify-between"><span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">Date</span><span className="font-display font-bold">{latestScene?.observation_date || "Pending"}</span></div>
              <div className="flex justify-between"><span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">Provider</span><span>{latestScene?.provider || "Sentinel"}</span></div>
              <div className="flex justify-between"><span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">Cloud Cover</span><span className="font-display font-bold">{Number(latestScene?.cloud_percentage || 0).toFixed(1)}% ({sceneQuality})</span></div>
              <div className="flex justify-between"><span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">Valid Pixels</span><span className="font-display font-bold text-primary">{Math.round(Number(latestScene?.valid_pixels_pct || 0))}%</span></div>
              <div className="flex justify-between"><span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">History Points</span><span>{history.length}</span></div>
            </div>
          </div>

          <div className="space-y-3 rounded-sm border border-border bg-card p-4">
            <span className="block text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground">Data Quality</span>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Cloud-free cells</span>
                <span className="font-display font-bold">{cloudFreeCount}/{displayCells.length || 0}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-sm bg-muted">
                <div className="h-full rounded-sm bg-primary" style={{ width: `${displayCells.length ? (cloudFreeCount / displayCells.length) * 100 : 0}%` }} />
              </div>
              <div className="mt-2 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Avg. valid pixels</span>
                <span className="font-display font-bold">{avgValidPixels}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-sm bg-muted">
                <div className="h-full rounded-sm bg-blue-500" style={{ width: `${avgValidPixels}%` }} />
              </div>
            </div>
          </div>

          <div className="space-y-3 rounded-sm border border-border bg-card p-4">
            <span className="block text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground">Predictions & Alerts</span>
            <div className="space-y-2">
              <div className="flex items-center gap-2 rounded-r-sm border-l-2 border-destructive bg-destructive/5 px-2 py-1.5">
                <span className="pulse-live h-1.5 w-1.5 rounded-full bg-destructive" />
                <span className="text-[10px] font-display font-semibold text-destructive">Moisture trend: {moistureTrend}</span>
              </div>
              <div className="flex items-center gap-2 rounded-r-sm border-l-2 border-amber-500 bg-amber-500/5 px-2 py-1.5">
                <Sun className="h-3 w-3 text-amber-600" />
                <span className="text-[10px] font-display font-semibold text-amber-700">Soil exposure: {soilTrend}</span>
              </div>
              <div className="flex items-center gap-2 rounded-r-sm border-l-2 border-primary bg-primary/5 px-2 py-1.5">
                <Leaf className="h-3 w-3 text-primary" />
                <span className="text-[10px] font-display font-semibold text-primary">Vegetation trend: {vegetationTrend}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
