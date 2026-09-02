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

// ---------------------------------------------------------------------------
// Plain-language message library — farmer-facing wording for every metric at
// every status. `headline` is the short label, `banner` the one-line alert,
// `tip` the suggested action, `paragraph` a full sentence about this field.
// Consumed by interpretLandMetric() / getMetricMessage().
// ---------------------------------------------------------------------------
export const METRIC_MESSAGES = {
  ndvi: {
    excellent: { headline: "Very Lush Crop", banner: "Your crop looks very green and thick.", tip: "No action needed — this field is doing very well.", paragraph: "Your field is very green and lush right now — a strong sign of healthy growth." },
    good: { headline: "Healthy Green Crop", banner: "Your crop looks healthy and green.", tip: "Keep up your current care — the crop is growing well.", paragraph: "Your crop looks healthy and green right now, which is a good sign." },
    watch: { headline: "Moderate Greenness", banner: "Your crop's greenness is average, not fully healthy.", tip: "Keep an eye on this field over the next few days.", paragraph: "Your crop's greenness is only moderate right now, so it's worth watching closely over the next few days." },
    needs_attention: { headline: "Low Greenness", banner: "Your crop is showing low greenness.", tip: "Check this field soon to find out what's holding the crop back.", paragraph: "Your crop is showing low greenness right now, which usually means it's under some kind of stress." },
    critical: { headline: "Almost No Crop", banner: "This field shows almost no green crop cover.", tip: "Visit this field urgently — the crop may have failed or dried out.", paragraph: "This field shows almost no green crop right now — a serious warning sign that needs urgent attention." },
  },
  evi: {
    excellent: { headline: "Very Strong Growth", banner: "Your crop is growing very strongly.", tip: "No action needed — growth is excellent right now.", paragraph: "Your crop is growing very strongly right now — an excellent sign for this season." },
    good: { headline: "Healthy Crop Growth", banner: "Your crop is growing at a healthy pace.", tip: "Continue your normal care — growth is on track.", paragraph: "Your crop is growing at a healthy, steady pace right now." },
    watch: { headline: "Average Crop Growth", banner: "Your crop's growth is average right now.", tip: "Keep watching this field for any change in the coming days.", paragraph: "Your crop's growth is only average right now, so it's worth keeping an eye on." },
    needs_attention: { headline: "Weak Crop Growth", banner: "Your crop's growth is weaker than it should be.", tip: "Check this field soon to understand why growth has slowed.", paragraph: "Your crop's growth is weaker than expected right now, which may need attention soon." },
    critical: { headline: "Severely Stunted Growth", banner: "Your crop's growth has almost stopped.", tip: "Visit this field urgently to check what is stopping growth.", paragraph: "Your crop's growth has almost stopped right now — a serious concern." },
  },
  savi: {
    excellent: { headline: "Strong Early Growth", banner: "Young plants are coming up very well.", tip: "No action needed — early growth is excellent.", paragraph: "Young plants are coming up very well right now — a great start to the season." },
    good: { headline: "Good Early Growth", banner: "Young plants are coming up well.", tip: "Continue your normal care during this early stage.", paragraph: "Young plants are coming up well right now." },
    watch: { headline: "Slow Early Growth", banner: "Young plants are coming up a little slowly.", tip: "Watch this field closely during the next few days.", paragraph: "Young plants are coming up a little slowly right now, so keep watching closely." },
    needs_attention: { headline: "Weak Seedling Growth", banner: "Seedlings are struggling to establish well.", tip: "Check this field soon — seedlings may need extra care.", paragraph: "Seedlings are struggling to establish well right now, and may need extra care." },
    critical: { headline: "Crop Establishment Failed", banner: "Seedlings do not appear to have established here.", tip: "Visit this field urgently to check if replanting is needed.", paragraph: "It looks like the crop has failed to establish in this field — replanting may be needed." },
  },
  ndmi: {
    excellent: { headline: "Well Hydrated Crop", banner: "Your crop is holding plenty of moisture.", tip: "No action needed — moisture levels are excellent.", paragraph: "Your crop is holding plenty of moisture right now — excellent condition." },
    good: { headline: "Adequate Crop Moisture", banner: "Your crop has enough moisture.", tip: "Continue your normal watering routine.", paragraph: "Your crop has enough moisture right now." },
    watch: { headline: "Slightly Dry Crop", banner: "Your crop is a little dry.", tip: "Keep an eye on watering over the next few days.", paragraph: "Your crop is a little dry right now, so it's worth watching." },
    needs_attention: { headline: "Very Dry Crop", banner: "Your crop is quite dry right now.", tip: "Water this field soon to prevent further stress.", paragraph: "Your crop is quite dry right now — water it soon to prevent further stress." },
    critical: { headline: "Severely Dry Crop", banner: "Your crop is severely short of moisture.", tip: "Water this field urgently to protect the crop.", paragraph: "Your crop is severely short of moisture right now — water it urgently to protect it." },
  },
  ndwi: {
    excellent: { headline: "Plenty of Water", banner: "There is plenty of water available in your field.", tip: "No action needed — water levels are excellent.", paragraph: "There is plenty of water available in your field right now." },
    good: { headline: "Adequate Water Available", banner: "Your field has adequate water available.", tip: "Continue your normal watering schedule.", paragraph: "Your field has adequate water available right now." },
    watch: { headline: "Limited Water Available", banner: "Water availability in your field is limited.", tip: "Plan your next watering soon.", paragraph: "Water availability in your field is limited right now — plan your next watering soon." },
    needs_attention: { headline: "Very Low Water", banner: "Water availability in your field is very low.", tip: "Water this field soon to avoid crop stress.", paragraph: "Water availability in your field is very low right now — water it soon to avoid crop stress." },
    critical: { headline: "Almost No Water", banner: "Water is very low in part of your field.", tip: "Water this field urgently — the crop is at risk.", paragraph: "Water is very low in part of your field right now — water it urgently, the crop is at risk." },
  },
  msi: {
    excellent: { headline: "No Water Stress", banner: "Your crop shows no signs of water stress.", tip: "No action needed — the crop is comfortable.", paragraph: "Your crop shows no signs of water stress right now." },
    good: { headline: "Mild Water Stress", banner: "Your crop shows only mild water stress.", tip: "Continue your normal watering routine.", paragraph: "Your crop shows only mild water stress right now." },
    watch: { headline: "Moderate Water Stress", banner: "Your crop is showing moderate water stress.", tip: "Keep a close watch on watering over the next few days.", paragraph: "Your crop is showing moderate water stress right now — keep a close watch on watering." },
    needs_attention: { headline: "High Water Stress", banner: "Your crop is under high water stress.", tip: "Water this field soon to relieve the stress.", paragraph: "Your crop is under high water stress right now — water it soon to relieve the stress." },
    critical: { headline: "Severe Water Stress", banner: "Your crop is under severe water stress.", tip: "Water this field urgently — the crop is struggling badly.", paragraph: "Your crop is under severe water stress right now — water it urgently, it's struggling badly." },
  },
  ndre: {
    excellent: { headline: "Excellent Crop Nutrition", banner: "Your crop is very well nourished.", tip: "No action needed — nutrition levels are excellent.", paragraph: "Your crop is very well nourished right now." },
    good: { headline: "Good Crop Nutrition", banner: "Your crop has good nutrition.", tip: "Continue your current fertilising routine.", paragraph: "Your crop has good nutrition right now." },
    watch: { headline: "Moderate Nutrient Level", banner: "Your crop's nutrient level is moderate.", tip: "Keep an eye on the crop and consider a nutrient check soon.", paragraph: "Your crop's nutrient level is moderate right now — consider a nutrient check soon." },
    needs_attention: { headline: "Low Crop Nutrition", banner: "Your crop's nutrition is running low.", tip: "Consider feeding this field soon to boost nutrients.", paragraph: "Your crop's nutrition is running low right now — consider feeding this field soon." },
    critical: { headline: "Severe Nutrient Deficiency", banner: "Your crop is severely short of nutrients.", tip: "Feed this field urgently to prevent further damage.", paragraph: "Your crop is severely short of nutrients right now — feed it urgently to prevent further damage." },
  },
  bsi: {
    excellent: { headline: "Fully Covered Soil", banner: "Your soil is fully covered by crop.", tip: "No action needed — coverage is excellent.", paragraph: "Your soil is fully covered by crop right now — excellent coverage." },
    good: { headline: "Mostly Covered Soil", banner: "Most of your soil is covered by crop.", tip: "No action needed — coverage is good.", paragraph: "Most of your soil is covered by crop right now." },
    watch: { headline: "Partly Exposed Soil", banner: "Some bare soil is showing in your field.", tip: "Keep an eye on bare patches as the season goes on.", paragraph: "Some bare soil is showing in your field right now — worth keeping an eye on." },
    needs_attention: { headline: "Mostly Bare Soil", banner: "Much of your field is showing bare soil.", tip: "Check this field soon to see why crop cover is low.", paragraph: "Much of your field is showing bare soil right now, which needs attention." },
    critical: { headline: "Completely Bare Soil", banner: "This field is showing completely bare soil.", tip: "Visit this field urgently to check on the crop.", paragraph: "This field is showing completely bare soil right now — visit it urgently to check on the crop." },
  },
  nbr: {
    excellent: { headline: "Excellent Crop Condition", banner: "Your crop's overall condition is excellent.", tip: "No action needed — everything looks great.", paragraph: "Your crop's overall condition is excellent right now." },
    good: { headline: "Healthy Crop Condition", banner: "Your crop's overall condition is healthy.", tip: "Continue your current care routine.", paragraph: "Your crop's overall condition is healthy right now." },
    watch: { headline: "Average Crop Condition", banner: "Your crop's overall condition is average.", tip: "Keep watching this field over the coming days.", paragraph: "Your crop's overall condition is average right now — keep watching over the coming days." },
    needs_attention: { headline: "Poor Crop Condition", banner: "Your crop's overall condition is poor.", tip: "Check this field soon to find out what's affecting it.", paragraph: "Your crop's overall condition is poor right now, which needs attention." },
    critical: { headline: "Severely Damaged Crop", banner: "Your crop's overall condition is severely damaged.", tip: "Visit this field urgently — the crop is in serious trouble.", paragraph: "Your crop's overall condition is severely damaged right now — visit this field urgently." },
  },
};

export function getMetricMessage(key, status) {
  return (
    METRIC_MESSAGES[key]?.[status] || {
      headline: "No data",
      banner: "This part of the field has not been checked yet.",
      tip: "",
      paragraph: "This part of the field has not been checked yet.",
    }
  );
}

// ---------------------------------------------------------------------------
// Field-interpretation builder — turns a set of metric readings (for one grid
// cell or a whole farm) into a single farmer-facing summary paragraph.
// Everything about how it reads is configurable here.
// ---------------------------------------------------------------------------
export const FIELD_INTERPRETATION_CONFIG = {
  concernStatuses: ["critical", "needs_attention", "watch"],
  maxIssues: 3,
  allGood: "Every signal on this land looks stable or healthy right now — no action needed.",
  singleIssueLead: "",
  multiIssueLead: "A few things need a look here. ",
  joiner: " ",
  cloudNote: "The satellite picture was partly blocked by cloud, so some readings are less certain.",
  cloudThreshold: 40,
};

const INTERPRETATION_PRIORITY = {
  critical: 5,
  needs_attention: 4,
  watch: 3,
  good: 2,
  excellent: 1,
  unavailable: 0,
};

export function buildFieldInterpretation(readings = [], { cloudPercentage = null, config = FIELD_INTERPRETATION_CONFIG } = {}) {
  const concerns = readings
    .filter((reading) => config.concernStatuses.includes(reading?.result?.status))
    .sort((a, b) => INTERPRETATION_PRIORITY[b.result.status] - INTERPRETATION_PRIORITY[a.result.status])
    .slice(0, config.maxIssues);

  const cloudy = Number(cloudPercentage) > config.cloudThreshold;
  let body;

  if (!concerns.length) {
    body = config.allGood;
  } else {
    const sentences = concerns.map((reading) => reading.result.paragraph).filter(Boolean);
    const lead = concerns.length > 1 ? config.multiIssueLead : config.singleIssueLead;
    body = (lead + sentences.join(config.joiner)).trim();
  }

  return cloudy ? `${body} ${config.cloudNote}`.trim() : body;
}

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
      headline: "No data",
      banner: "This part of the field has not been checked yet.",
      tip: "",
      paragraph: "This part of the field has not been checked yet.",
      label: "No data",
      shortLabel: "No data",
      color: "#94a3b8",
      textClass: "text-slate-500",
      badgeClass: "border-slate-200 bg-slate-50 text-slate-600",
      surfaceClass: "border-slate-200 bg-slate-50/70",
    };
  }

  const status = metric.rules.find((rule) => rule.test(value))?.status || "critical";
  const message = getMetricMessage(key, status);

  return {
    metric,
    value,
    status,
    interpretation: metric.interpretations[status],
    headline: message.headline || metric.interpretations[status],
    banner: message.banner || metric.interpretations[status],
    tip: message.tip || "",
    paragraph: message.paragraph || "",
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
