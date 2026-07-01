import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { 
  MapPin, Hexagon, User, Calendar, Satellite, Leaf, Droplets, 
  Mountain, Cloud, Layers, Grid3X3, ChevronRight, Download,
  RefreshCw, Eye, Thermometer, Sun, Check
} from "lucide-react";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import IndexReadout from "@/components/ui-custom/IndexReadout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { motion } from "framer-motion";

const FARM_DATA = {
  id: "MF-0042",
  farmerId: "FR-001",
  farmerName: "Ramesh Sahoo",
  village: "Baliguali",
  block: "Puri Sadar",
  district: "Puri",
  state: "Odisha",
  surveyNumber: "RS-1204/56",
  area: 2.4,
  h3Resolution: 10,
  h3CellCount: 18,
  crop: "Paddy (Kharif)",
  registeredDate: "2024-03-15",
};

const SATELLITE_DATA = {
  sceneId: "S2B_MSIL2A_20250115T044121_N0400_R033",
  date: "2025-01-15",
  cloudCover: 12.4,
  provider: "Sentinel-2B",
  processingLevel: "L2A",
  validPixels: 94,
};

const H3_CELLS = Array.from({ length: 18 }, (_, i) => ({
  id: `8a2a1072b59${String(i).padStart(4, "0")}fff`,
  ndvi: 0.42 + Math.random() * 0.35,
  moisture: 0.28 + Math.random() * 0.3,
  bareSoil: Math.random() * 0.25,
  heat: 28 + Math.random() * 6,
  validPixels: 85 + Math.floor(Math.random() * 15),
  cloudFree: Math.random() > 0.15,
}));

const avgNdvi = H3_CELLS.reduce((s, c) => s + c.ndvi, 0) / H3_CELLS.length;
const avgMoisture = H3_CELLS.reduce((s, c) => s + c.moisture, 0) / H3_CELLS.length;
const avgBareSoil = H3_CELLS.reduce((s, c) => s + c.bareSoil, 0) / H3_CELLS.length;
const avgHeat = H3_CELLS.reduce((s, c) => s + c.heat, 0) / H3_CELLS.length;

function HexGrid({ cells, hoveredCell, setHoveredCell, selectedCell, setSelectedCell }) {
  const cols = 6;
  return (
    <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {cells.map((cell, i) => {
        const green = Math.floor(cell.ndvi * 255);
        const bg = `rgb(${255 - green}, ${100 + green * 0.6}, ${80})`;
        const isHovered = hoveredCell === i;
        const isSelected = selectedCell === i;
        return (
          <motion.div
            key={i}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: i * 0.02 }}
            onMouseEnter={() => setHoveredCell(i)}
            onMouseLeave={() => setHoveredCell(null)}
            onClick={() => setSelectedCell(isSelected ? null : i)}
            className={`relative aspect-square rounded-sm cursor-pointer transition-all ${
              isSelected ? "ring-2 ring-foreground ring-offset-1" :
              isHovered ? "ring-1 ring-primary ring-offset-1" : ""
            }`}
            style={{ backgroundColor: bg }}
          >
            {!cell.cloudFree && (
              <Cloud className="absolute top-0.5 right-0.5 w-2.5 h-2.5 text-white/70" />
            )}
            {isHovered && (
              <div className="absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-2 w-40 p-2 bg-card border border-border rounded-sm shadow-lg">
                <div className="space-y-1 text-[9px]">
                  <div className="flex justify-between"><span className="text-muted-foreground">Cell</span><span className="font-mono">{i + 1}/{cells.length}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">NDVI</span><span className="font-display font-bold text-primary">{cell.ndvi.toFixed(3)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Moisture</span><span className="font-display font-bold text-blue-600">{cell.moisture.toFixed(3)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Bare Soil</span><span className="font-display font-bold">{(cell.bareSoil * 100).toFixed(1)}%</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Valid Px</span><span>{cell.validPixels}%</span></div>
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
  const [hoveredCell, setHoveredCell] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);
  const [viewMode, setViewMode] = useState("h3");

  const activeCell = selectedCell !== null ? H3_CELLS[selectedCell] : null;

  return (
    <div className="p-4 md:p-6 space-y-4 max-w-[1400px] mx-auto">
      {/* Farm Identity Strip */}
      <div className="bg-card border border-border rounded-sm p-3">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-display uppercase tracking-widest text-muted-foreground">Farm</span>
            <span className="font-display font-bold text-foreground">{FARM_DATA.id}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <User className="w-3 h-3 text-muted-foreground" />
            <Link to={`/farmer-profile/${FARM_DATA.farmerId}`} className="text-foreground hover:text-primary transition-colors">
              {FARM_DATA.farmerName}
            </Link>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3 h-3 text-muted-foreground" />
            <span>{FARM_DATA.village}, {FARM_DATA.block}, {FARM_DATA.district}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Hexagon className="w-3 h-3 text-muted-foreground" />
            <span>{FARM_DATA.area} ha · {FARM_DATA.h3CellCount} cells · Res {FARM_DATA.h3Resolution}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Satellite className="w-3 h-3 text-muted-foreground" />
            <span>{SATELLITE_DATA.date} · {SATELLITE_DATA.cloudCover}% cloud</span>
          </div>
          <VerificationStamp label="VERIFIED" type="success" compact />
        </div>
      </div>

      {/* Pipeline */}
      <PipelineStepper
        steps={["Location", "Farmer", "Boundary", "H3 Grid", "Satellite", "Raster", "Intelligence"]}
        currentStep={7}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main — Map + Grid */}
        <div className="lg:col-span-2 space-y-4">
          {/* Map with boundary */}
          <div className="bg-card border border-border rounded-sm overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xs font-display font-bold uppercase tracking-wider text-foreground">Land View</span>
                <div className="flex items-center gap-1 bg-muted rounded-sm p-0.5">
                  <button
                    onClick={() => setViewMode("h3")}
                    className={`px-2 py-1 rounded-sm text-[10px] font-display uppercase tracking-wider transition-colors ${viewMode === "h3" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"}`}
                  >
                    <Hexagon className="w-3 h-3 inline mr-1" />H3 Grid
                  </button>
                  <button
                    onClick={() => setViewMode("map")}
                    className={`px-2 py-1 rounded-sm text-[10px] font-display uppercase tracking-wider transition-colors ${viewMode === "map" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"}`}
                  >
                    <Layers className="w-3 h-3 inline mr-1" />Satellite
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" className="h-7 text-[10px] font-display uppercase tracking-wider rounded-sm">
                  <RefreshCw className="w-3 h-3 mr-1" />Latest Scene
                </Button>
                <Button size="sm" variant="outline" className="h-7 text-[10px] font-display uppercase tracking-wider rounded-sm">
                  <Download className="w-3 h-3 mr-1" />Export
                </Button>
              </div>
            </div>

            <div className="p-4 bg-muted/30 topo-texture">
              {viewMode === "h3" ? (
                <div className="max-w-md mx-auto">
                  <HexGrid
                    cells={H3_CELLS}
                    hoveredCell={hoveredCell}
                    setHoveredCell={setHoveredCell}
                    selectedCell={selectedCell}
                    setSelectedCell={setSelectedCell}
                  />
                  {/* Legend */}
                  <div className="flex items-center justify-center gap-2 mt-3">
                    <span className="text-[8px] font-display uppercase tracking-wider text-muted-foreground">Low NDVI</span>
                    <div className="flex gap-0.5">
                      {[0.2, 0.35, 0.5, 0.65, 0.8].map(v => (
                        <div key={v} className="w-5 h-2 rounded-sm" style={{ backgroundColor: `rgb(${255 - v * 255}, ${100 + v * 153}, 80)` }} />
                      ))}
                    </div>
                    <span className="text-[8px] font-display uppercase tracking-wider text-muted-foreground">High NDVI</span>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center">
                  <div className="text-center">
                    <Satellite className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">Satellite composite view</p>
                    <p className="text-[10px] text-muted-foreground/60">{SATELLITE_DATA.sceneId}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Selected Cell Detail */}
          {activeCell && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-primary/30 rounded-sm overflow-hidden"
            >
              <div className="px-4 py-2.5 border-b border-border bg-primary/5 flex items-center justify-between">
                <span className="text-xs font-display font-bold uppercase tracking-wider text-primary">Cell {selectedCell + 1} — Detailed Analysis</span>
                <button onClick={() => setSelectedCell(null)} className="text-[10px] text-muted-foreground hover:text-foreground">Close</button>
              </div>
              <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <IndexReadout label="Vegetation" value={activeCell.ndvi} icon={<Leaf />} color="bg-primary" />
                </div>
                <div className="space-y-1">
                  <IndexReadout label="Moisture" value={activeCell.moisture} icon={<Droplets />} color="bg-blue-500" />
                </div>
                <div className="space-y-1">
                  <IndexReadout label="Bare Soil" value={activeCell.bareSoil} icon={<Mountain />} color="bg-amber-600" />
                </div>
                <div className="space-y-1">
                  <IndexReadout label="Surface Temp" value={activeCell.heat} unit="°C" min={25} max={40} icon={<Thermometer />} color="bg-red-500" />
                </div>
              </div>
              <div className="px-4 pb-3 flex items-center gap-4 text-[9px] font-display uppercase tracking-wider text-muted-foreground">
                <span>Valid pixels: {activeCell.validPixels}%</span>
                <span>Cloud-free: {activeCell.cloudFree ? "Yes" : "No"}</span>
                <span>H3 ID: ...{activeCell.id.slice(-8)}</span>
              </div>
            </motion.div>
          )}

          {/* H3 Feature Table */}
          <div className="bg-card border border-border rounded-sm overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
              <span className="text-xs font-display font-bold uppercase tracking-wider text-foreground">H3 Cell Feature Table</span>
              <span className="text-[9px] font-display uppercase tracking-wider text-muted-foreground">{H3_CELLS.length} cells · Resolution {FARM_DATA.h3Resolution}</span>
            </div>
            <div className="overflow-x-auto max-h-64 overflow-y-auto scrollbar-hide">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm">
                  <tr className="border-b border-border">
                    {["Cell", "NDVI", "Moisture", "Bare Soil", "Temp °C", "Valid Px %", "Cloud"].map(h => (
                      <th key={h} className="text-left px-3 py-2 font-display font-semibold uppercase tracking-wider text-[9px] text-muted-foreground">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {H3_CELLS.map((cell, i) => (
                    <tr
                      key={i}
                      onClick={() => setSelectedCell(i)}
                      className={`border-b border-border last:border-0 cursor-pointer transition-colors ${selectedCell === i ? "bg-primary/5" : "hover:bg-muted/30"}`}
                    >
                      <td className="px-3 py-1.5 font-display font-bold">{String(i + 1).padStart(2, "0")}</td>
                      <td className={`px-3 py-1.5 font-display font-bold ${cell.ndvi > 0.5 ? "text-primary" : cell.ndvi > 0.3 ? "text-amber-600" : "text-destructive"}`}>{cell.ndvi.toFixed(3)}</td>
                      <td className="px-3 py-1.5 font-display font-bold text-blue-600">{cell.moisture.toFixed(3)}</td>
                      <td className="px-3 py-1.5">{(cell.bareSoil * 100).toFixed(1)}%</td>
                      <td className="px-3 py-1.5">{cell.heat.toFixed(1)}</td>
                      <td className="px-3 py-1.5">{cell.validPixels}</td>
                      <td className="px-3 py-1.5">{cell.cloudFree ? <Check className="w-3 h-3 text-primary" /> : <Cloud className="w-3 h-3 text-muted-foreground" />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Panel — Index Readouts */}
        <div className="space-y-4">
          {/* Farm-level index readouts */}
          <div className="bg-card border border-border rounded-sm p-4 space-y-4">
            <span className="text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground block">Farm-Level Indices</span>
            <IndexReadout label="Vegetation (NDVI)" value={avgNdvi} icon={<Leaf />} color="bg-primary" />
            <IndexReadout label="Moisture (NDMI)" value={avgMoisture} icon={<Droplets />} color="bg-blue-500" />
            <IndexReadout label="Bare Soil Index" value={avgBareSoil} icon={<Mountain />} color="bg-amber-600" />
            <IndexReadout label="Avg. Surface Temp" value={avgHeat} unit="°C" min={25} max={40} icon={<Thermometer />} color="bg-red-500" />
          </div>

          {/* Satellite Scene Card */}
          <div className="bg-card border border-border rounded-sm p-4 space-y-3">
            <span className="text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground block">Satellite Scene</span>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-muted-foreground font-display uppercase tracking-wider text-[9px]">Scene ID</span><span className="font-mono text-[9px]">...{SATELLITE_DATA.sceneId.slice(-16)}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground font-display uppercase tracking-wider text-[9px]">Date</span><span className="font-display font-bold">{SATELLITE_DATA.date}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground font-display uppercase tracking-wider text-[9px]">Provider</span><span>{SATELLITE_DATA.provider}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground font-display uppercase tracking-wider text-[9px]">Cloud Cover</span><span className="font-display font-bold">{SATELLITE_DATA.cloudCover}%</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground font-display uppercase tracking-wider text-[9px]">Valid Pixels</span><span className="font-display font-bold text-primary">{SATELLITE_DATA.validPixels}%</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground font-display uppercase tracking-wider text-[9px]">Processing</span><span>{SATELLITE_DATA.processingLevel}</span></div>
            </div>
          </div>

          {/* Data Quality */}
          <div className="bg-card border border-border rounded-sm p-4 space-y-3">
            <span className="text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground block">Data Quality</span>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Cloud-free cells</span>
                <span className="font-display font-bold">{H3_CELLS.filter(c => c.cloudFree).length}/{H3_CELLS.length}</span>
              </div>
              <div className="h-2 bg-muted rounded-sm overflow-hidden">
                <div className="h-full bg-primary rounded-sm" style={{ width: `${(H3_CELLS.filter(c => c.cloudFree).length / H3_CELLS.length) * 100}%` }} />
              </div>
              <div className="flex items-center justify-between text-xs mt-2">
                <span className="text-muted-foreground">Avg. valid pixels</span>
                <span className="font-display font-bold">{Math.round(H3_CELLS.reduce((s, c) => s + c.validPixels, 0) / H3_CELLS.length)}%</span>
              </div>
              <div className="h-2 bg-muted rounded-sm overflow-hidden">
                <div className="h-full bg-blue-500 rounded-sm" style={{ width: `${Math.round(H3_CELLS.reduce((s, c) => s + c.validPixels, 0) / H3_CELLS.length)}%` }} />
              </div>
            </div>
          </div>

          {/* Predictions Placeholder */}
          <div className="bg-card border border-border rounded-sm p-4 space-y-3">
            <span className="text-[10px] font-display uppercase tracking-[0.2em] text-muted-foreground block">Predictions & Alerts</span>
            <div className="space-y-2">
              <div className="flex items-center gap-2 px-2 py-1.5 bg-destructive/5 border-l-2 border-destructive rounded-r-sm">
                <span className="w-1.5 h-1.5 bg-destructive rounded-full pulse-live" />
                <span className="text-[10px] text-destructive font-display font-semibold">Moisture stress in 4 cells — south-east quadrant</span>
              </div>
              <div className="flex items-center gap-2 px-2 py-1.5 bg-amber-500/5 border-l-2 border-amber-500 rounded-r-sm">
                <Sun className="w-3 h-3 text-amber-600" />
                <span className="text-[10px] text-amber-700 font-display font-semibold">High surface temperature — 34.2°C peak</span>
              </div>
              <div className="flex items-center gap-2 px-2 py-1.5 bg-primary/5 border-l-2 border-primary rounded-r-sm">
                <Leaf className="w-3 h-3 text-primary" />
                <span className="text-[10px] text-primary font-display font-semibold">Vegetation growth trend: +0.08 NDVI over 30 days</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}