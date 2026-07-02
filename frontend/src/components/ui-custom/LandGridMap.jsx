import React, { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Polygon, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function normalizeRing(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return geometry.coordinates?.[0] || [];
  if (geometry.type === "MultiPolygon") return geometry.coordinates?.[0]?.[0] || [];
  return [];
}

function toLatLng(ring) {
  return ring.map(([lon, lat]) => [lat, lon]);
}

function boundsFromRing(ring) {
  if (!ring.length) return null;
  const lons = ring.map(([lon]) => lon);
  const lats = ring.map(([, lat]) => lat);
  return [
    [Math.min(...lats), Math.min(...lons)],
    [Math.max(...lats), Math.max(...lons)],
  ];
}

function colorFor(value, parameter) {
  const num = Number(value);
  if (value === null || value === undefined || Number.isNaN(num)) return "rgba(148,163,184,0.35)";
  const normalized = Math.max(0, Math.min(1, parameter === "temperature" || parameter === "cloud" ? num / 100 : (num + 0.2) / 1.2));
  if (parameter === "bsi") return `rgba(${Math.round(34 + normalized * 170)}, ${Math.round(197 - normalized * 120)}, 94, 0.62)`;
  if (parameter === "cloud") return `rgba(${Math.round(190 + normalized * 50)}, ${Math.round(190 + normalized * 50)}, ${Math.round(190 + normalized * 50)}, 0.55)`;
  if (parameter === "temperature") return `rgba(${Math.round(90 + normalized * 150)}, ${Math.round(80 + normalized * 70)}, 90, 0.55)`;
  return `rgba(${Math.round(220 - normalized * 120)}, ${Math.round(180 + normalized * 55)}, ${Math.round(90 + normalized * 50)}, 0.62)`;
}

function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [20, 20], animate: true });
  }, [bounds, map]);
  return null;
}

function MapClickClear({ onClick }) {
  const map = useMap();
  useEffect(() => {
    const handleClick = (event) => onClick?.(event);
    map.on("click", handleClick);
    return () => map.off("click", handleClick);
  }, [map, onClick]);
  return null;
}

export default function LandGridMap({
  farm,
  gridCells = [],
  h3Cells = [],
  selectedParameter = "ndvi",
  onGridCellClick,
  selectedGridCellId,
  showH3Layer = false,
  onGridCellHover,
}) {
  const [ready, setReady] = useState(false);
  const polygon = normalizeRing(farm?.polygon_geojson);
  const bounds = useMemo(() => boundsFromRing(polygon) || [[19.8, 85.75], [19.9, 85.95]], [polygon]);
  const gridLatLng = useMemo(() => gridCells.map((cell) => ({
    ...cell,
    ring: toLatLng(normalizeRing(cell.cell_polygon_geojson)),
  })), [gridCells]);
  const h3LatLng = useMemo(() => h3Cells.map((cell) => ({
    ...cell,
    ring: toLatLng(normalizeRing(cell.geometry || cell.cell_polygon_geojson)),
  })), [h3Cells]);

  useEffect(() => {
    const id = window.requestAnimationFrame(() => setReady(true));
    return () => window.cancelAnimationFrame(id);
  }, []);

  return (
    <div className="space-y-3">
      <div className="rounded-2xl border border-gray-200 bg-white px-3 py-2 text-xs text-gray-500">
        Satellite basemap: Esri World Imagery. Visual grid is the default view.
      </div>
      <div className="overflow-hidden rounded-3xl border border-gray-200 shadow-xl">
        <MapContainer
          center={bounds[0]}
          zoom={17}
          className="h-[640px] w-full"
          scrollWheelZoom
          zoomControl
          attributionControl={false}
        >
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution='Tiles &copy; Esri'
            maxZoom={19}
          />
          <FitBounds bounds={bounds} />
          <MapClickClear onClick={() => {}} />
          {polygon.length >= 3 && (
            <Polygon positions={toLatLng(polygon)} pathOptions={{ color: "#ff3b30", weight: 3, fillColor: "#ff3b30", fillOpacity: 0.15 }} />
          )}
          {gridLatLng.map((cell) => {
            const selected = String(selectedGridCellId) === String(cell.grid_cell_id);
            const value = cell[selectedParameter];
            return (
              <Polygon
                key={cell.grid_cell_id}
                positions={cell.ring}
                pathOptions={{
                  color: selected ? "#ffffff" : "rgba(15,23,42,0.8)",
                  weight: selected ? 3 : 1,
                  fillColor: colorFor(value, selectedParameter),
                  fillOpacity: 0.7,
                  dashArray: selected ? undefined : "2 4",
                }}
                eventHandlers={{
                  mouseover: () => onGridCellHover?.(cell),
                  mouseout: () => onGridCellHover?.(null),
                  click: () => onGridCellClick?.(cell),
                }}
              />
            );
          })}
          {showH3Layer && h3LatLng.map((cell) => (
            <Polygon
              key={`h3-${cell.h3_index || cell.grid_cell_id}`}
              positions={cell.ring}
              pathOptions={{ color: "#22c55e", weight: 1.5, fillOpacity: 0, dashArray: "6 4" }}
            />
          ))}
          {polygon.length >= 3 && <Marker position={toLatLng(polygon)[0]} />}
          {!ready && <div />}
        </MapContainer>
      </div>
    </div>
  );
}
