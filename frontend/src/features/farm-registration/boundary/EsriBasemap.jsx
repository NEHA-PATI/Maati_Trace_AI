import { useEffect } from "react";
import { useMap } from "react-leaflet";
import { basemapLayer } from "esri-leaflet";
import { MAP_CONFIG } from "@/lib/mapConfig";

export default function EsriBasemap({ onError }) {
  const map = useMap();
  useEffect(() => {
    if (!MAP_CONFIG.apiKey) return undefined;
    let imagery;
    let labels;
    const handleTileError = () => onError?.("Satellite imagery could not be loaded. Check the ArcGIS key restrictions and allowed domain.");
    try {
      imagery = basemapLayer("Imagery", { token: MAP_CONFIG.apiKey });
      labels = basemapLayer("ImageryLabels", { token: MAP_CONFIG.apiKey });
      imagery.on("tileerror", handleTileError);
      labels.on("tileerror", handleTileError);
      imagery.addTo(map);
      labels.addTo(map);
    } catch {
      onError?.("Satellite imagery could not be initialized. Check the ArcGIS frontend configuration.");
      return undefined;
    }
    return () => {
      imagery?.off("tileerror", handleTileError);
      labels?.off("tileerror", handleTileError);
      if (labels) map.removeLayer(labels);
      if (imagery) map.removeLayer(imagery);
    };
  }, [map, onError]);
  return null;
}
