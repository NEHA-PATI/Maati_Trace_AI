import { useEffect } from "react";
import { useMap } from "react-leaflet";
import { MAP_CONFIG } from "@/lib/mapConfig";

function getZoom(precision) {
  if (precision === "gps") return MAP_CONFIG.zoom.farm;
  if (precision === "village") return MAP_CONFIG.zoom.village;
  if (precision === "block") return MAP_CONFIG.zoom.block;
  if (precision === "district") return MAP_CONFIG.zoom.district;
  return MAP_CONFIG.zoom.default;
}

export default function MapCamera({ target, bounds, polygonBounds }) {
  const map = useMap();
  useEffect(() => {
    const timeout = window.setTimeout(() => map.invalidateSize(), 150);
    return () => window.clearTimeout(timeout);
  }, [map]);
  useEffect(() => {
    if (polygonBounds?.length === 2) {
      map.fitBounds(polygonBounds, { padding: [32, 32], maxZoom: MAP_CONFIG.zoom.farm, animate: true });
      return;
    }
    if (bounds?.length === 2) {
      map.fitBounds(bounds, { padding: [32, 32], maxZoom: getZoom(target?.precision), animate: true });
      return;
    }
    if (Number.isFinite(target?.latitude) && Number.isFinite(target?.longitude)) {
      map.flyTo([target.latitude, target.longitude], getZoom(target.precision), { animate: true, duration: 1.2 });
    }
  }, [bounds, map, polygonBounds, target]);
  return null;
}
