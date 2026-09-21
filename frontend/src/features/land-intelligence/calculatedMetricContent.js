// Farmer-facing copy and score-range wording for calculated crop intelligence.
// Keep score classification in calculatedMetrics.js; edit this file when the
// language, range labels, or signal explanations need to change.

const CONDITION_RANGES = [
  { min: 80, max: 100, status: "good", label: "Good", rangeText: "80 to 100", headline: "Very healthy", paragraph: "This signal is in a healthy range for the crop.", fieldSentence: "The crop is showing a healthy overall signal." },
  { min: 60, max: 79.999, status: "fair", label: "Fair", rangeText: "60 to 79", headline: "Mostly healthy", paragraph: "This signal is fair, with some room for improvement.", fieldSentence: "Most conditions are supportive, with a few things worth watching." },
  { min: 40, max: 59.999, status: "attention", label: "Needs attention", rangeText: "40 to 59", headline: "Needs attention", paragraph: "This signal is weaker than the preferred crop range.", fieldSentence: "At least one crop signal needs attention." },
  { min: 20, max: 39.999, status: "poor", label: "Poor", rangeText: "20 to 39", headline: "Poor", paragraph: "This signal is substantially below the preferred crop range.", fieldSentence: "The crop is showing a poor condition signal." },
  { min: 0, max: 19.999, status: "critical", label: "Critical", rangeText: "0 to 19", headline: "Critical", paragraph: "This signal is in a critical range and needs prompt field checking.", fieldSentence: "A critical crop condition signal needs prompt field checking." },
];

const RISK_RANGES = [
  { min: 0, max: 19.999, status: "normal", label: "Normal", rangeText: "0 to 19", headline: "Normal", paragraph: "This risk signal is currently low.", fieldSentence: "No major risk signal is visible from this measure." },
  { min: 20, max: 39.999, status: "watch", label: "Watch", rangeText: "20 to 39", headline: "Watch", paragraph: "This risk signal is beginning to rise.", fieldSentence: "One or more risk signals should be watched." },
  { min: 40, max: 59.999, status: "attention", label: "Attention", rangeText: "40 to 59", headline: "Needs attention", paragraph: "This risk signal is high enough to check the field soon.", fieldSentence: "A risk signal is high enough to check the field soon." },
  { min: 60, max: 79.999, status: "high", label: "High", rangeText: "60 to 79", headline: "High risk", paragraph: "This risk signal is high and may affect the crop.", fieldSentence: "A high risk signal may affect the crop." },
  { min: 80, max: 100, status: "critical", label: "Critical", rangeText: "80 to 100", headline: "Critical risk", paragraph: "This risk signal is critical and needs prompt field checking.", fieldSentence: "A critical risk signal needs prompt field checking." },
];

const METRICS = {
  crop_condition: {
    displayName: "Crop Condition",
    signalMeaning: "A combined crop-health score. Higher values mean the crop signals are more supportive overall.",
    ranges: { condition: CONDITION_RANGES },
  },
  water_stress: {
    displayName: "Water Stress Risk",
    signalMeaning: "Evidence that the crop may be short of usable water, using canopy moisture, root-zone moisture, rainfall, heat, evapotranspiration, and radar signals.",
    ranges: { risk: RISK_RANGES },
  },
  moisture_condition: {
    displayName: "Crop Moisture",
    signalMeaning: "The current moisture condition around the crop, combining canopy and root-zone moisture observations.",
    ranges: { condition: CONDITION_RANGES },
  },
  growth_condition: {
    displayName: "Growth Condition",
    signalMeaning: "How supportive the observed vegetation level and growth direction are for the selected crop.",
    ranges: { condition: CONDITION_RANGES },
  },
  growth_anomaly: {
    displayName: "Growth Anomaly",
    signalMeaning: "How unusual the current crop growth is compared with its recent history, nearby H3 cells, and expected trajectory.",
    ranges: { risk: RISK_RANGES },
  },
  heat_stress: {
    displayName: "Heat Stress Risk",
    signalMeaning: "Evidence of heat load on the crop from H3-level thermal observations and atmospheric demand.",
    ranges: { risk: RISK_RANGES },
  },
  waterlogging_risk: {
    displayName: "Waterlogging Risk",
    signalMeaning: "Evidence of excess water or poor drainage from optical water, wet-soil, rainfall, terrain, historic water, and radar signals.",
    ranges: { risk: RISK_RANGES },
  },
  soil_condition: {
    displayName: "Soil Condition",
    signalMeaning: "A modeled soil and terrain suitability signal using mapped soil properties and drainage context; it is not a laboratory test.",
    ranges: { condition: CONDITION_RANGES },
  },
  nutrient_stress_risk: {
    displayName: "Nutrient Stress Risk",
    signalMeaning: "Evidence that crop growth and mapped soil properties may be consistent with nutrient stress; it is not an N, P, or K diagnosis.",
    ranges: { risk: RISK_RANGES },
  },
  erosion_risk: {
    displayName: "Land / Erosion Risk",
    signalMeaning: "Relative susceptibility to soil loss based mainly on terrain slope, land cover, soil context, and moisture conditions.",
    ranges: { risk: RISK_RANGES },
  },
};

for (const content of Object.values(METRICS)) {
  content.messages = Object.fromEntries(
    Object.values(content.ranges)[0].map((range) => [range.status, {
      headline: range.headline,
      paragraph: range.paragraph,
      fieldSentence: range.fieldSentence,
    }]),
  );
}

export const CALCULATED_METRIC_CONTENT = METRICS;

export const CALCULATED_FIELD_CONTENT = {
  allGood: "The calculated crop signals look stable overall right now.",
  singleIssueLead: "",
  multiIssueLead: "A few calculated crop signals need a closer look. ",
  joiner: " ",
  maxIssues: 3,
};
