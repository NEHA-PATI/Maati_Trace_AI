export const METRIC_STATUSES = {
  excellent: {
    label: "Excellent",
    shortLabel: "Excellent",
    color: "#3b82f6",
    textClass: "text-blue-700",
    badgeClass: "border-blue-200 bg-blue-50 text-blue-700",
    surfaceClass: "border-blue-200 bg-blue-50/70",
  },
  good: {
    label: "Good",
    shortLabel: "Good",
    color: "#22c55e",
    textClass: "text-emerald-700",
    badgeClass: "border-emerald-200 bg-emerald-50 text-emerald-700",
    surfaceClass: "border-emerald-200 bg-emerald-50/70",
  },
  watch: {
    label: "Watch",
    shortLabel: "Watch",
    color: "#eab308",
    textClass: "text-yellow-700",
    badgeClass: "border-yellow-200 bg-yellow-50 text-yellow-700",
    surfaceClass: "border-yellow-200 bg-yellow-50/70",
  },
  needs_attention: {
    label: "Needs Attention",
    shortLabel: "Attention",
    color: "#f97316",
    textClass: "text-orange-700",
    badgeClass: "border-orange-200 bg-orange-50 text-orange-700",
    surfaceClass: "border-orange-200 bg-orange-50/70",
  },
  critical: {
    label: "Critical",
    shortLabel: "Critical",
    color: "#e11d48",
    textClass: "text-rose-700",
    badgeClass: "border-rose-200 bg-rose-50 text-rose-700",
    surfaceClass: "border-rose-200 bg-rose-50/70",
  },
};

const HIGHER_IS_BETTER = (excellent, good, watch, attention) => [
  { status: "excellent", test: (value) => value > excellent },
  { status: "good", test: (value) => value >= good },
  { status: "watch", test: (value) => value >= watch },
  { status: "needs_attention", test: (value) => value >= attention },
  { status: "critical", test: () => true },
];

const LOWER_IS_BETTER = (excellent, good, watch, attention) => [
  { status: "excellent", test: (value) => value < excellent },
  { status: "good", test: (value) => value <= good },
  { status: "watch", test: (value) => value <= watch },
  { status: "needs_attention", test: (value) => value <= attention },
  { status: "critical", test: () => true },
];

export const LAND_METRICS = [
  {
    key: "ndvi",
    backendKey: "ndvi",
    name: "Crop Greenness",
    acronym: "NDVI",
    description: "How green and vigorous the crop canopy appears.",
    interpretations: {
      excellent: "Very Lush Crop",
      good: "Healthy Green Crop",
      watch: "Moderate Greenness",
      needs_attention: "Low Greenness",
      critical: "Almost No Crop",
    },
    ranges: ["> 0.80", "0.60-0.80", "0.40-0.60", "0.20-0.40", "< 0.20"],
    rules: HIGHER_IS_BETTER(0.8, 0.6, 0.4, 0.2),
  },
  {
    key: "evi",
    backendKey: "evi",
    name: "Crop Growth",
    acronym: "EVI",
    description: "A canopy-sensitive view of active crop growth.",
    interpretations: {
      excellent: "Very Strong Growth",
      good: "Healthy Crop Growth",
      watch: "Average Crop Growth",
      needs_attention: "Weak Crop Growth",
      critical: "Severely Stunted Growth",
    },
    ranges: ["> 0.60", "0.40-0.60", "0.25-0.40", "0.10-0.25", "< 0.10"],
    rules: HIGHER_IS_BETTER(0.6, 0.4, 0.25, 0.1),
  },
  {
    key: "savi",
    backendKey: "savi",
    name: "Early Crop Growth",
    acronym: "SAVI",
    description: "Crop emergence and growth where soil is still visible.",
    interpretations: {
      excellent: "Strong Early Growth",
      good: "Good Early Growth",
      watch: "Slow Early Growth",
      needs_attention: "Weak Seedling Growth",
      critical: "Crop Establishment Failed",
    },
    ranges: ["> 0.60", "0.40-0.60", "0.25-0.40", "0.10-0.25", "< 0.10"],
    rules: HIGHER_IS_BETTER(0.6, 0.4, 0.25, 0.1),
  },
  {
    key: "ndmi",
    backendKey: "ndmi",
    name: "Crop Moisture",
    acronym: "NDMI",
    description: "Moisture held in the crop canopy.",
    interpretations: {
      excellent: "Well Hydrated Crop",
      good: "Adequate Crop Moisture",
      watch: "Slightly Dry Crop",
      needs_attention: "Very Dry Crop",
      critical: "Severely Dry Crop",
    },
    ranges: ["> 0.40", "0.20-0.40", "0.00-0.20", "-0.20-0.00", "< -0.20"],
    rules: HIGHER_IS_BETTER(0.4, 0.2, 0, -0.2),
  },
  {
    key: "ndwi",
    backendKey: "ndwi",
    name: "Water Availability",
    acronym: "NDWI",
    description: "The relative presence of water in the observed area.",
    interpretations: {
      excellent: "Plenty of Water",
      good: "Adequate Water Available",
      watch: "Limited Water Available",
      needs_attention: "Very Low Water",
      critical: "Almost No Water",
    },
    ranges: ["> 0.50", "0.20-0.50", "0.00-0.20", "-0.20-0.00", "< -0.20"],
    rules: HIGHER_IS_BETTER(0.5, 0.2, 0, -0.2),
  },
  {
    key: "msi",
    backendKey: "msi",
    name: "Water Stress",
    acronym: "MSI",
    description: "Crop water stress; lower values are healthier.",
    interpretations: {
      excellent: "No Water Stress",
      good: "Mild Water Stress",
      watch: "Moderate Water Stress",
      needs_attention: "High Water Stress",
      critical: "Severe Water Stress",
    },
    ranges: ["< 0.40", "0.40-0.80", "0.80-1.20", "1.20-1.80", "> 1.80"],
    rules: LOWER_IS_BETTER(0.4, 0.8, 1.2, 1.8),
  },
  {
    key: "ndre",
    backendKey: "ndre",
    name: "Crop Nutrition",
    acronym: "NDRE",
    description: "A chlorophyll-sensitive signal related to crop nutrition.",
    interpretations: {
      excellent: "Excellent Crop Nutrition",
      good: "Good Crop Nutrition",
      watch: "Moderate Nutrient Level",
      needs_attention: "Low Crop Nutrition",
      critical: "Severe Nutrient Deficiency",
    },
    ranges: ["> 0.50", "0.35-0.50", "0.20-0.35", "0.10-0.20", "< 0.10"],
    rules: HIGHER_IS_BETTER(0.5, 0.35, 0.2, 0.1),
  },
  {
    key: "bsi",
    backendKey: "bsi",
    name: "Bare Land",
    acronym: "BSI",
    description: "Visible bare-soil exposure; lower values are healthier.",
    interpretations: {
      excellent: "Fully Covered Soil",
      good: "Mostly Covered Soil",
      watch: "Partly Exposed Soil",
      needs_attention: "Mostly Bare Soil",
      critical: "Completely Bare Soil",
    },
    ranges: ["< -0.20", "-0.20-0.00", "0.00-0.20", "0.20-0.40", "> 0.40"],
    rules: LOWER_IS_BETTER(-0.2, 0, 0.2, 0.4),
  },
  {
    key: "nbr",
    backendKey: "nbr",
    name: "Crop Condition",
    acronym: "NBR",
    description: "The available backend stress-ratio signal for crop condition.",
    interpretations: {
      excellent: "Excellent Crop Condition",
      good: "Healthy Crop Condition",
      watch: "Average Crop Condition",
      needs_attention: "Poor Crop Condition",
      critical: "Severely Damaged Crop",
    },
    ranges: ["> 0.60", "0.40-0.60", "0.20-0.40", "0.00-0.20", "< 0.00"],
    rules: HIGHER_IS_BETTER(0.6, 0.4, 0.2, 0),
  },
];

export const LAND_METRIC_KEYS = LAND_METRICS.map((metric) => metric.key);

export function getLandMetric(key) {
  return LAND_METRICS.find((metric) => metric.key === key) || null;
}

export function interpretLandMetric(key, rawValue) {
  const metric = getLandMetric(key);
  const value = Number(rawValue);

  if (!metric || rawValue === null || rawValue === undefined || Number.isNaN(value)) {
    return {
      metric,
      value: null,
      status: "unavailable",
      interpretation: "No data",
      label: "No data",
      shortLabel: "No data",
      color: "#94a3b8",
      textClass: "text-slate-500",
      badgeClass: "border-slate-200 bg-slate-50 text-slate-600",
      surfaceClass: "border-slate-200 bg-slate-50/70",
    };
  }

  const status = metric.rules.find((rule) => rule.test(value))?.status || "critical";

  return {
    metric,
    value,
    status,
    interpretation: metric.interpretations[status],
    ...METRIC_STATUSES[status],
  };
}

export function metricValueFromCell(cell, key) {
  if (!cell) return null;
  return cell[key] ?? cell[`weighted_${key}`] ?? null;
}

export function metricValueFromSummary(summary, key) {
  if (!summary) return null;
  return summary[`weighted_${key}`] ?? summary[`avg_${key}`] ?? null;
}
