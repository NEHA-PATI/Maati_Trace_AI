import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

// Real Leaflet map showing all farm outlines for a farmer
// Grids are originated from world lat/lng tile system
// Each farm gets an outlined polygon + a clickable marker

export default function FarmerLandMap({ farms = [] }) {
  const mapRef = useRef(null);
  const instanceRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (instanceRef.current) return;

    // Load Leaflet CSS
    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }

    const initMap = () => {
      const L = window.L;
      if (!mapRef.current || instanceRef.current) return;

      // Center on first farm or default Puri
      const center = farms[0]?.center || [19.81, 85.85];

      const map = L.map(mapRef.current, {
        center,
        zoom: 13,
        zoomControl: true,
        scrollWheelZoom: false,
        attributionControl: false,
      });

      instanceRef.current = map;

      // Satellite-style tile
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
      }).addTo(map);

      // Draw each farm polygon + marker
      farms.forEach((farm, idx) => {
        const coords = farm.polygon || generateDemoPolygon(farm.center || center, farm.area || 2.0, idx);

        // Polygon outline
        const poly = L.polygon(coords, {
          color: farm.status === "verified" ? "#10b981" : "#f59e0b",
          fillColor: farm.status === "verified" ? "#10b981" : "#f59e0b",
          fillOpacity: 0.15,
          weight: 2.5,
          dashArray: farm.status === "pending" ? "6,4" : null,
        }).addTo(map);

        // Centroid marker — clickable → /land/:id
        const centroid = getCentroid(coords);
        const markerHtml = `
          <div style="
            background: ${farm.status === 'verified' ? '#10b981' : '#f59e0b'};
            border: 3px solid white;
            border-radius: 50%;
            width: 28px; height: 28px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            cursor: pointer;
            font-family: Poppins, sans-serif;
            font-size: 9px;
            font-weight: 800;
            color: white;
          ">${idx + 1}</div>`;

        const icon = L.divIcon({ className: "", html: markerHtml, iconSize: [28, 28], iconAnchor: [14, 14] });
        const marker = L.marker(centroid, { icon }).addTo(map);

        marker.bindTooltip(`
          <div style="font-family:Poppins,sans-serif;font-size:11px;line-height:1.5">
            <b>${farm.id}</b><br/>
            ${farm.area} ha · ${farm.crop}<br/>
            <span style="font-size:9px;color:#6b7280">Click marker to open</span>
          </div>`, {
          direction: "top",
          offset: [0, -16],
          className: "leaflet-maatitrace-tooltip",
        });

        marker.on("click", () => navigate(`/land/${farm.id}`));
        poly.on("click", () => navigate(`/land/${farm.id}`));

        // Grid lines (lat/lng based, like OSM tile grid)
        drawGrid(L, map, coords);
      });

      // Fit map to all polygons
      if (farms.length > 0) {
        const allCoords = farms.flatMap(f =>
          f.polygon || generateDemoPolygon(f.center || center, f.area || 2.0, 0)
        );
        map.fitBounds(L.latLngBounds(allCoords), { padding: [40, 40] });
      }

      // Inject tooltip style
      if (!document.getElementById("maatitrace-leaflet-style")) {
        const style = document.createElement("style");
        style.id = "maatitrace-leaflet-style";
        style.textContent = `
          .leaflet-maatitrace-tooltip {
            background: rgba(255,255,255,0.97);
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 6px 12px;
            font-family: Poppins, sans-serif;
            font-size: 11px;
            color: #1f2937;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
          }
          .leaflet-maatitrace-tooltip::before { display: none; }
          .leaflet-container { cursor: default; }
        `;
        document.head.appendChild(style);
      }
    };

    if (window.L) {
      initMap();
    } else {
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.onload = initMap;
      document.head.appendChild(script);
    }

    return () => {
      if (instanceRef.current) {
        instanceRef.current.remove();
        instanceRef.current = null;
      }
    };
  }, []);

  return (
    <div ref={mapRef} className="w-full rounded-3xl overflow-hidden" style={{ height: "380px" }} />
  );
}

// Generate a demo irregular polygon around a center point
function generateDemoPolygon(center, areaHa, seed) {
  const [lat, lng] = center;
  const r = Math.sqrt(areaHa / Math.PI) * 0.004; // rough radius in degrees
  const offsets = [
    [0.2, 0.55], [0.8, 0.1], [1.0, 0.6], [0.8, 0.85],
    [0.28, 0.88], [0.05, 0.65], [0.08, 0.35]
  ];
  const seedOff = seed * 0.0005;
  return offsets.map(([dx, dy]) => [
    lat + (dy - 0.5) * r * 2 + seedOff,
    lng + (dx - 0.5) * r * 2 + seedOff,
  ]);
}

function getCentroid(coords) {
  const lat = coords.reduce((s, c) => s + c[0], 0) / coords.length;
  const lng = coords.reduce((s, c) => s + c[1], 0) / coords.length;
  return [lat, lng];
}

// Draw a light lat/lng grid inside the polygon bounds
function drawGrid(L, map, coords) {
  const bounds = L.latLngBounds(coords);
  const latMin = bounds.getSouth(), latMax = bounds.getNorth();
  const lngMin = bounds.getWest(), lngMax = bounds.getEast();
  const latStep = (latMax - latMin) / 6;
  const lngStep = (lngMax - lngMin) / 6;
  const style = { color: "rgba(0,0,0,0.18)", weight: 0.8, dashArray: "3,4" };

  for (let i = 0; i <= 6; i++) {
    const lat = latMin + i * latStep;
    L.polyline([[lat, lngMin - lngStep * 0.5], [lat, lngMax + lngStep * 0.5]], style).addTo(map);
  }
  for (let j = 0; j <= 6; j++) {
    const lng = lngMin + j * lngStep;
    L.polyline([[latMin - latStep * 0.5, lng], [latMax + latStep * 0.5, lng]], style).addTo(map);
  }
}
