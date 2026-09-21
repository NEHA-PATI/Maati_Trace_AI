import { CALCULATED_FIELD_CONTENT, CALCULATED_METRIC_CONTENT } from "./calculatedMetricContent";

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

const STATUS_STYLES = {
  good: { color: "#16a34a", className: "bg-emerald-50 text-emerald-700 border-emerald-200", textClass: "text-emerald-700", badgeClass: "border-emerald-200 bg-emerald-50 text-emerald-700", surfaceClass: "border-emerald-200 bg-emerald-50/70" },
  fair: { color: "#84cc16", className: "bg-lime-50 text-lime-700 border-lime-200", textClass: "text-lime-700", badgeClass: "border-lime-200 bg-lime-50 text-lime-700", surfaceClass: "border-lime-200 bg-lime-50/70" },
  normal: { color: "#16a34a", className: "bg-emerald-50 text-emerald-700 border-emerald-200", textClass: "text-emerald-700", badgeClass: "border-emerald-200 bg-emerald-50 text-emerald-700", surfaceClass: "border-emerald-200 bg-emerald-50/70" },
  watch: { color: "#84cc16", className: "bg-lime-50 text-lime-700 border-lime-200", textClass: "text-lime-700", badgeClass: "border-lime-200 bg-lime-50 text-lime-700", surfaceClass: "border-lime-200 bg-lime-50/70" },
  attention: { color: "#eab308", className: "bg-yellow-50 text-yellow-700 border-yellow-200", textClass: "text-yellow-700", badgeClass: "border-yellow-200 bg-yellow-50 text-yellow-700", surfaceClass: "border-yellow-200 bg-yellow-50/70" },
  poor: { color: "#f97316", className: "bg-orange-50 text-orange-700 border-orange-200", textClass: "text-orange-700", badgeClass: "border-orange-200 bg-orange-50 text-orange-700", surfaceClass: "border-orange-200 bg-orange-50/70" },
  high: { color: "#f97316", className: "bg-orange-50 text-orange-700 border-orange-200", textClass: "text-orange-700", badgeClass: "border-orange-200 bg-orange-50 text-orange-700", surfaceClass: "border-orange-200 bg-orange-50/70" },
  critical: { color: "#dc2626", className: "bg-rose-50 text-rose-700 border-rose-200", textClass: "text-rose-700", badgeClass: "border-rose-200 bg-rose-50 text-rose-700", surfaceClass: "border-rose-200 bg-rose-50/70" },
  unavailable: { color: "#94a3b8", className: "bg-slate-100 text-slate-600 border-slate-200", textClass: "text-slate-600", badgeClass: "border-slate-200 bg-slate-100 text-slate-600", surfaceClass: "border-slate-200 bg-slate-100" },
};

function contentFor(key, overrides) {
  const override = Array.isArray(overrides)
    ? overrides.find((item) => item.metric_key === key || item.key === key)
    : overrides?.[key];
  const base = CALCULATED_METRIC_CONTENT[key] || {};
  const normalizedOverride = override
    ? { ...override, signalMeaning: override.signalMeaning ?? override.signal_meaning }
    : {};
  return {
    ...base,
    ...normalizedOverride,
    ranges: { ...(base.ranges || {}), ...(normalizedOverride.ranges || {}) },
    messages: { ...(base.messages || {}), ...(normalizedOverride.messages || {}) },
  };
}

export function interpretCalculatedMetric(key, value, contentOverrides = null) {
  const metric = getCalculatedMetric(key);
  const num = Number(value);
  const content = contentFor(key, contentOverrides);
  if (!metric || value === null || value === undefined || Number.isNaN(num)) {
    return { label: "Unavailable", shortLabel: "Unavailable", status: "unavailable", ...STATUS_STYLES.unavailable, signalMeaning: content.signalMeaning || "This signal has not been calculated yet." };
  }
  const ranges = content.ranges?.[metric.direction] || CALCULATED_METRIC_CONTENT[key]?.ranges?.[metric.direction] || [];
  const range = ranges.find((item) => num >= Number(item.min) && num <= Number(item.max)) || ranges[ranges.length - 1];
  const status = range?.status || "unavailable";
  const message = content.messages?.[status] || {};
  return {
    label: range?.label || "Unavailable",
    shortLabel: range?.label || "Unavailable",
    status,
    ...(STATUS_STYLES[status] || STATUS_STYLES.unavailable),
    rangeText: range?.rangeText || "",
    headline: message.headline || range?.headline || range?.label || "Unavailable",
    paragraph: message.paragraph || range?.paragraph || "",
    fieldSentence: message.fieldSentence || range?.fieldSentence || "",
    signalMeaning: content.signalMeaning || metric.description,
  };
}

export function buildCalculatedFieldInterpretation(readings = [], { cropName = "", contentOverrides = null } = {}) {
  const content = { ...CALCULATED_FIELD_CONTENT, ...(contentOverrides?.fieldInterpretation || {}) };
  const availableReadings = readings.filter(({ result }) => result.status !== "unavailable");
  if (!availableReadings.length) return `${cropName ? `${cropName}: ` : ""}Calculated crop intelligence is not available yet.`;
  const concerns = readings
    .filter(({ metric, result }) => result.status !== "unavailable" && (metric.direction === "risk"
      ? ["attention", "high", "critical"].includes(result.status)
      : ["attention", "poor", "critical"].includes(result.status)))
    .slice(0, content.maxIssues || 3);
  if (!concerns.length) return `${cropName ? `${cropName}: ` : ""}${content.allGood}`;
  const sentences = concerns.map(({ result }) => result.fieldSentence || result.paragraph).filter(Boolean);
  const lead = concerns.length > 1 ? content.multiIssueLead : content.singleIssueLead;
  return `${cropName ? `${cropName}: ` : ""}${lead || ""}${sentences.join(content.joiner || " ")}`.trim();
}
