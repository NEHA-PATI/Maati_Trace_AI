export const MAP_CONFIG = {
  apiKey: import.meta.env.VITE_ARCGIS_API_KEY || "",
  defaultCenter: {
    lat: Number(import.meta.env.VITE_MAP_DEFAULT_LAT || 20.2961),
    lng: Number(import.meta.env.VITE_MAP_DEFAULT_LNG || 85.8245),
  },
  zoom: {
    default: Number(import.meta.env.VITE_MAP_DEFAULT_ZOOM || 7),
    district: Number(import.meta.env.VITE_MAP_DISTRICT_ZOOM || 10),
    block: Number(import.meta.env.VITE_MAP_BLOCK_ZOOM || 13),
    village: Number(import.meta.env.VITE_MAP_VILLAGE_ZOOM || 17),
    farm: Number(import.meta.env.VITE_MAP_FARM_ZOOM || 19),
    minimumDrawing: Number(import.meta.env.VITE_MAP_MIN_DRAW_ZOOM || 16),
    maximum: Number(import.meta.env.VITE_MAP_MAX_ZOOM || 22),
  },
  maximumGpsAccuracy: Number(import.meta.env.VITE_MAX_GPS_ACCURACY_METERS || 20),
  sampleBoundaryEnabled: import.meta.env.VITE_ENABLE_SAMPLE_BOUNDARY === "true",
};

export function validateMapConfiguration() {
  if (!MAP_CONFIG.apiKey) {
    throw new Error("VITE_ARCGIS_API_KEY is missing from the frontend environment.");
  }
}
