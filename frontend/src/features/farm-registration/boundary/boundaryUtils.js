import area from "@turf/area";
import bbox from "@turf/bbox";
import booleanValid from "@turf/boolean-valid";
import { polygon } from "@turf/helpers";

const SQUARE_METERS_PER_ACRE = 4046.8564224;

export function closeRing(coordinates) {
  if (!Array.isArray(coordinates) || !coordinates.length) return [];
  const cleaned = coordinates.map(([lng, lat]) => [Number(lng), Number(lat)]);
  if (cleaned.length < 3) return cleaned;
  const first = cleaned[0];
  const last = cleaned[cleaned.length - 1];
  if (first[0] === last[0] && first[1] === last[1]) return cleaned;
  return [...cleaned, [...first]];
}

export function removeClosingCoordinate(coordinates) {
  if (!Array.isArray(coordinates) || !coordinates.length) return [];
  const first = coordinates[0];
  const last = coordinates[coordinates.length - 1];
  if (coordinates.length > 1 && first[0] === last[0] && first[1] === last[1]) {
    return coordinates.slice(0, -1);
  }
  return coordinates;
}

export function geometryToFeature(geometry) {
  if (!geometry || geometry.type !== "Polygon" || !Array.isArray(geometry.coordinates)) return null;
  try {
    return polygon(geometry.coordinates);
  } catch {
    return null;
  }
}

export function calculateBoundarySummary(geometry) {
  const feature = geometryToFeature(geometry);
  if (!feature) return { valid: false, message: "Draw the farm boundary first." };

  const ring = feature.geometry.coordinates[0] || [];
  const uniquePoints = removeClosingCoordinate(ring);
  if (uniquePoints.length < 3) return { valid: false, message: "Add at least three farm corners." };
  if (uniquePoints.length > 499) return { valid: false, message: "The boundary contains too many points." };

  const coordinatesValid = uniquePoints.every(([lng, lat]) => (
    Number.isFinite(lng) && Number.isFinite(lat)
      && lng >= -180 && lng <= 180 && lat >= -90 && lat <= 90
  ));
  if (!coordinatesValid) return { valid: false, message: "The boundary contains invalid coordinates." };
  if (!booleanValid(feature)) return { valid: false, message: "Some boundary lines cross each other. Move the green corner points." };

  const squareMeters = area(feature);
  if (!(squareMeters > 1)) return { valid: false, message: "The selected farm boundary is too small." };

  return {
    valid: true,
    message: "Farm boundary is ready.",
    pointCount: uniquePoints.length,
    squareMeters,
    acres: squareMeters / SQUARE_METERS_PER_ACRE,
    hectares: squareMeters / 10000,
    boundingBox: bbox(feature),
    geometry: feature.geometry,
  };
}

export function geoJsonBounds(geometry) {
  const feature = geometryToFeature(geometry);
  if (!feature) return null;
  const [minLng, minLat, maxLng, maxLat] = bbox(feature);
  return [[minLat, minLng], [maxLat, maxLng]];
}
