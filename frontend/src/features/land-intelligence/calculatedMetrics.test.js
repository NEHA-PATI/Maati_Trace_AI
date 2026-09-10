import { describe, expect, it } from "vitest";

import {
  CALCULATED_METRIC_KEYS,
  calculatedValueFromCell,
  interpretCalculatedMetric,
} from "./calculatedMetrics";

describe("calculated crop-intelligence metrics", () => {
  it("exposes all deterministic V1 outputs", () => {
    expect(CALCULATED_METRIC_KEYS).toEqual([
      "crop_condition",
      "water_stress",
      "moisture_condition",
      "growth_condition",
      "growth_anomaly",
      "heat_stress",
      "waterlogging_risk",
      "soil_condition",
      "nutrient_stress_risk",
      "erosion_risk",
    ]);
  });

  it.each([
    ["water_stress", 10, "Normal"],
    ["water_stress", 25, "Watch"],
    ["water_stress", 45, "Attention"],
    ["water_stress", 65, "High"],
    ["water_stress", 85, "Critical"],
  ])("classifies risk score %s=%s as %s", (metric, score, expected) => {
    expect(interpretCalculatedMetric(metric, score).label).toBe(expected);
  });

  it.each([
    ["crop_condition", 90, "Good"],
    ["crop_condition", 70, "Fair"],
    ["crop_condition", 50, "Needs attention"],
    ["crop_condition", 30, "Poor"],
    ["crop_condition", 10, "Critical"],
  ])("classifies condition score %s=%s as %s", (metric, score, expected) => {
    expect(interpretCalculatedMetric(metric, score).label).toBe(expected);
  });

  it("reads a flattened grid score first and nested calculation second", () => {
    expect(calculatedValueFromCell({ water_stress_score: 71 }, "water_stress")).toBe(71);
    expect(
      calculatedValueFromCell({ calculations: { water_stress: { score: 63 } } }, "water_stress"),
    ).toBe(63);
  });
});
