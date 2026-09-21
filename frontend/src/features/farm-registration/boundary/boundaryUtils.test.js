import { describe, expect, it } from "vitest";
import { calculateBoundarySummary, closeRing, geoJsonBounds } from "./boundaryUtils";

const SQUARE = {
  type: "Polygon",
  coordinates: [[
    [85.8200, 20.2900],
    [85.8210, 20.2900],
    [85.8210, 20.2910],
    [85.8200, 20.2910],
    [85.8200, 20.2900],
  ]],
};

describe("farm boundary utilities", () => {
  it("closes a GeoJSON ring without duplicating an already closed point", () => {
    expect(closeRing(SQUARE.coordinates[0])).toHaveLength(5);
    expect(closeRing(SQUARE.coordinates[0].slice(0, 4))).toHaveLength(5);
  });

  it("calculates geodesic-preview-friendly area values and bounds", () => {
    const summary = calculateBoundarySummary(SQUARE);
    expect(summary.valid).toBe(true);
    expect(summary.pointCount).toBe(4);
    expect(summary.acres).toBeGreaterThan(0);
    expect(summary.hectares).toBeGreaterThan(0);
    expect(geoJsonBounds(SQUARE)).toEqual([
      [20.29, 85.82],
      [20.291, 85.821],
    ]);
  });

  it("rejects self-intersecting boundaries", () => {
    const bowTie = {
      type: "Polygon",
      coordinates: [[
        [85.8200, 20.2900],
        [85.8210, 20.2910],
        [85.8210, 20.2900],
        [85.8200, 20.2910],
        [85.8200, 20.2900],
      ]],
    };
    expect(calculateBoundarySummary(bowTie).valid).toBe(false);
  });

  it("rejects an empty geometry", () => {
    expect(calculateBoundarySummary(null)).toMatchObject({ valid: false });
  });
});
