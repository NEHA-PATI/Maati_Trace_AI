export const CALCULATED_METRICS = Object.freeze([
  { key: "crop_condition", scoreKey: "crop_condition_score", name: "Crop Condition", direction: "condition", description: "Crop-specific deterministic condition score calculated from engineered H3 features." },
  { key: "water_stress", scoreKey: "water_stress_score", name: "Water Stress Risk", direction: "risk", description: "Multi-source water-stress evidence from canopy moisture, rainfall, root-zone moisture, thermal, ET and SAR context." },
  { key: "moisture_condition", scoreKey: "moisture_condition_score", name: "Crop Moisture", direction: "condition", description: "Current canopy/root-zone moisture condition." },
  { key: "growth_condition", scoreKey: "growth_condition_score", name: "Growth Condition", direction: "condition", description: "Crop-specific canopy/vegetative growth and trajectory condition." },
  { key: "growth_anomaly", scoreKey: "growth_anomaly_score", name: "Growth Anomaly", direction: "risk", description: "Temporal, spatial and expected-trajectory anomaly score." },
  { key: "heat_stress", scoreKey: "heat_stress_score", name: "Heat Stress Risk", direction: "risk", description: "Thermal and atmospheric-demand stress evidence." },
  { key: "waterlogging_risk", scoreKey: "waterlogging_risk_score", name: "Waterlogging Risk", direction: "risk", description: "Excess-water and poor-drainage evidence." },
  { key: "soil_condition", scoreKey: "soil_condition_score", name: "Soil Condition", direction: "condition", description: "Modeled soil/terrain suitability context; not a laboratory soil test." },
  { key: "nutrient_stress_risk", scoreKey: "nutrient_stress_risk_score", name: "Nutrient Stress Risk", direction: "risk", description: "Possible nutrient-related stress evidence; not an N/P/K deficiency diagnosis." },
  { key: "erosion_risk", scoreKey: "erosion_risk_score", name: "Land / Erosion Risk", direction: "risk", description: "Relative land-erosion susceptibility proxy." },
]);

export const CALCULATED_METRIC_KEYS = Object.freeze(CALCULATED_METRICS.map((item) => item.key));

export function getCalculatedMetric(key) {
  return CALCULATED_METRICS.find((item) => item.key === key) || null;
}

export function calculatedValueFromCell(cell, key) {
  const metric = getCalculatedMetric(key);
  if (!metric || !cell) return null;
  return cell[metric.scoreKey] ?? cell?.calculations?.[key]?.score ?? null;
}

export function interpretCalculatedMetric(key, value) {
  const metric = getCalculatedMetric(key);
  const num = Number(value);
  if (!metric || value === null || value === undefined || Number.isNaN(num)) {
    return { label: "Unavailable", color: "#94a3b8", className: "bg-slate-100 text-slate-600 border-slate-200" };
  }
  if (metric.direction === "risk") {
    if (num < 20) return { label: "Normal", color: "#16a34a", className: "bg-emerald-50 text-emerald-700 border-emerald-200" };
    if (num < 40) return { label: "Watch", color: "#84cc16", className: "bg-lime-50 text-lime-700 border-lime-200" };
    if (num < 60) return { label: "Attention", color: "#eab308", className: "bg-yellow-50 text-yellow-700 border-yellow-200" };
    if (num < 80) return { label: "High", color: "#f97316", className: "bg-orange-50 text-orange-700 border-orange-200" };
    return { label: "Critical", color: "#dc2626", className: "bg-rose-50 text-rose-700 border-rose-200" };
  }
  if (num >= 80) return { label: "Good", color: "#16a34a", className: "bg-emerald-50 text-emerald-700 border-emerald-200" };
  if (num >= 60) return { label: "Fair", color: "#84cc16", className: "bg-lime-50 text-lime-700 border-lime-200" };
  if (num >= 40) return { label: "Needs attention", color: "#eab308", className: "bg-yellow-50 text-yellow-700 border-yellow-200" };
  if (num >= 20) return { label: "Poor", color: "#f97316", className: "bg-orange-50 text-orange-700 border-orange-200" };
  return { label: "Critical", color: "#dc2626", className: "bg-rose-50 text-rose-700 border-rose-200" };
}
