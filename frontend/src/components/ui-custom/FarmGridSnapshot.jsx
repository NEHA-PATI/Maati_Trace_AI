import React, { useEffect, useMemo, useRef, useState } from "react";
import { MapContainer, Polygon, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { getFarmGridCells, getLatestGridValues } from "@/lib/api/analytics";
import { interpretLandMetric, metricValueFromCell } from "@/features/land-intelligence/metricInterpretation";
import FarmPolygonThumb from "@/components/ui-custom/FarmPolygonThumb";

// Same source used by the Land Intelligence page's live grid map — free, no API key.
const SATELLITE_TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

function normalizeRing(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return geometry.coordinates?.[0] || [];
  if (geometry.type === "MultiPolygon") return geometry.coordinates?.[0]?.[0] || [];
  return [];
}

function toLatLng(ring) {
  return ring.map(([lon, lat]) => [lat, lon]);
}

// A real, non-interactive preview of a farm's analysed land grid: the same
// satellite basemap and per-cell health colouring as the Land Intelligence
// page, sized down for a card. It is loaded lazily (only once the card
// scrolls into view) and falls back to the lightweight vector shape while
// data is loading, or for farms that have not been analysed yet — so it
// never spends a farmer's data budget on cards they don't look at.
export default function FarmGridSnapshot({ farmId, polygon = [], tone = "good", className = "" }) {
  const hostRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const [cells, setCells] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const el = hostRef.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return undefined;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || !farmId) return undefined;
    let cancelled = false;

    (async () => {
      try {
        const [gridCells, gridValues] = await Promise.all([
          getFarmGridCells(farmId).catch(() => []),
          getLatestGridValues(farmId).catch(() => []),
        ]);
        if (cancelled) return;
        const valuesById = new Map((gridValues || []).map((value) => [String(value.grid_cell_id), value]));
        const merged = (gridCells || [])
          .map((cell) => ({ ...cell, ...(valuesById.get(String(cell.grid_cell_id)) || {}) }))
          .filter((cell) => normalizeRing(cell.cell_polygon_geojson).length >= 3);
        setCells(merged);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [visible, farmId]);

  const bounds = useMemo(() => {
    const points = Array.isArray(polygon)
      ? polygon.filter((point) => Array.isArray(point) && Number.isFinite(point[0]) && Number.isFinite(point[1]))
      : [];
    if (!points.length) return null;
    const lats = points.map((point) => point[0]);
    const lngs = points.map((point) => point[1]);
    return [
      [Math.min(...lats), Math.min(...lngs)],
      [Math.max(...lats), Math.max(...lngs)],
    ];
  }, [polygon]);

  const hasSnapshot = bounds && Array.isArray(cells) && cells.length > 0 && !failed;

  return (
    <div ref={hostRef} className={`relative overflow-hidden ${className}`}>
      {hasSnapshot ? (
        <MapContainer
          bounds={bounds}
          boundsOptions={{ padding: [8, 8] }}
          className="h-full w-full"
          dragging={false}
          touchZoom={false}
          doubleClickZoom={false}
          scrollWheelZoom={false}
          boxZoom={false}
          keyboard={false}
          zoomControl={false}
          attributionControl={false}
        >
          <TileLayer url={SATELLITE_TILE_URL} maxZoom={19} />
          {polygon.length >= 3 && (
            <Polygon positions={polygon} pathOptions={{ color: "#ff3b30", weight: 2, fillOpacity: 0 }} />
          )}
          {cells.map((cell) => {
            const value = metricValueFromCell(cell, "ndvi");
            const result = interpretLandMetric("ndvi", value);
            return (
              <Polygon
                key={cell.grid_cell_id}
                positions={toLatLng(normalizeRing(cell.cell_polygon_geojson))}
                pathOptions={{
                  color: "rgba(15,23,42,0.35)",
                  weight: 0.5,
                  fillColor: result.color,
                  fillOpacity: 0.68,
                }}
              />
            );
          })}
        </MapContainer>
      ) : (
        <FarmPolygonThumb polygon={polygon} tone={tone} className="h-full w-full" />
      )}
    </div>
  );
}
