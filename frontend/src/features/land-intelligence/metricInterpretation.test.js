import { describe, expect, it } from "vitest";

import {
  buildFieldInterpretation,
  FIELD_INTERPRETATION_CONFIG,
  interpretLandMetric,
} from "./metricInterpretation";

const reading = (key, value) => ({ metric: { key }, value, result: interpretLandMetric(key, value) });

describe("interpretLandMetric", () => {
  it.each([
    ["ndvi", 0.81, "excellent"],
    ["ndvi", 0.8, "good"],
    ["ndvi", 0.6, "good"],
    ["ndvi", 0.4, "watch"],
    ["ndvi", 0.2, "needs_attention"],
    ["ndvi", 0.19, "critical"],
    ["ndmi", -0.2, "needs_attention"],
    ["ndmi", -0.21, "critical"],
    ["msi", 0.39, "excellent"],
    ["msi", 0.4, "good"],
    ["msi", 1.8, "needs_attention"],
    ["msi", 1.81, "critical"],
    ["bsi", -0.21, "excellent"],
    ["bsi", -0.2, "good"],
    ["bsi", 0.4, "needs_attention"],
    ["bsi", 0.41, "critical"],
  ])("classifies %s value %s as %s", (metric, value, expected) => {
    expect(interpretLandMetric(metric, value).status).toBe(expected);
  });

  it("returns no data for an unavailable reading", () => {
    expect(interpretLandMetric("ndvi", null).status).toBe("unavailable");
    expect(interpretLandMetric("ndvi", null).interpretation).toBe("No data");
  });

  it.each([
    ["ndvi", 0.82, "Very Lush Crop"],
    ["evi", 0.3, "Average Crop Growth"],
    ["savi", 0.12, "Weak Seedling Growth"],
    ["ndmi", -0.3, "Severely Dry Crop"],
    ["ndwi", 0.3, "Adequate Water Available"],
    ["msi", 1.9, "Severe Water Stress"],
    ["ndre", 0.15, "Low Crop Nutrition"],
    ["bsi", -0.3, "Fully Covered Soil"],
    ["nbr", -0.1, "Severely Damaged Crop"],
  ])("describes %s value %s as %s", (metric, value, expected) => {
    expect(interpretLandMetric(metric, value).interpretation).toBe(expected);
  });
});

describe("buildFieldInterpretation", () => {
  it("returns the all-good line when every reading is healthy", () => {
    const text = buildFieldInterpretation([reading("ndvi", 0.7), reading("ndmi", 0.5)]);
    expect(text).toBe(FIELD_INTERPRETATION_CONFIG.allGood);
  });

  it("surfaces the worst readings for the selected cell", () => {
    const text = buildFieldInterpretation([
      reading("ndvi", 0.1), // critical
      reading("ndmi", 0.3), // good
    ]);
    expect(text).toContain(interpretLandMetric("ndvi", 0.1).paragraph);
    expect(text).not.toBe(FIELD_INTERPRETATION_CONFIG.allGood);
  });

  it("adds the cloud note when the scene was cloudy", () => {
    const text = buildFieldInterpretation([reading("ndvi", 0.7)], { cloudPercentage: 60 });
    expect(text).toContain(FIELD_INTERPRETATION_CONFIG.cloudNote);
  });
});
