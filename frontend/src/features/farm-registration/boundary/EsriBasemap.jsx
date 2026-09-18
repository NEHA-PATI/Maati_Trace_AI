import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import { basemapLayer } from "esri-leaflet";
import { MAP_CONFIG } from "@/lib/mapConfig";

const TILE_ERROR_COOLDOWN_MS = 5000;

export default function EsriBasemap({ onError }) {
  const map = useMap();
  const lastErrorAtRef = useRef(0);
  useEffect(() => {
    if (!MAP_CONFIG.apiKey) return undefined;

    const layerOptions = {
      token: MAP_CONFIG.apiKey,
      maxZoom: MAP_CONFIG.zoom.maximum,
      maxNativeZoom: MAP_CONFIG.zoom.nativeImagery,
    };

    let imagery;
    let labels;
    const handleTileError = (event) => {
      const now = Date.now();
      if (now - lastErrorAtRef.current < TILE_ERROR_COOLDOWN_MS) return;
      lastErrorAtRef.current = now;

      const status = event?.error?.status;
      const message = status === 401 || status === 403
        ? "Satellite imagery access was denied. Check the ArcGIS key restrictions."
        : "Satellite imagery is unavailable at this zoom level or location.";
      onError?.(message);
    };

    try {
      imagery = basemapLayer("Imagery", layerOptions);
      labels = basemapLayer("ImageryLabels", layerOptions);
      imagery.on("tileerror", handleTileError);
      labels.on("tileerror", handleTileError);
      imagery.addTo(map);
      labels.addTo(map);
    } catch {
      onError?.("Satellite imagery could not be initialized.");
      return undefined;
    }
    return () => {
      imagery?.off("tileerror", handleTileError);
      labels?.off("tileerror", handleTileError);
      if (labels && map.hasLayer(labels)) map.removeLayer(labels);
      if (imagery && map.hasLayer(imagery)) map.removeLayer(imagery);
    };
  }, [map, onError]);
  return null;
}
