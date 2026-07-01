import React, { useEffect, useRef } from "react";

// Leaflet district coverage map — uses OpenStreetMap tiles (free, no API key)
const CLUSTER_POINTS = [
  { lat: 19.81, lng: 85.85, label: "Puri Sadar", count: 142, size: 44 },
  { lat: 20.05, lng: 85.52, label: "Nimapara", count: 104, size: 36 },
  { lat: 20.12, lng: 85.09, label: "Nayagarh", count: 89, size: 32 },
  { lat: 19.98, lng: 85.95, label: "Delang", count: 67, size: 28 },
  { lat: 19.63, lng: 86.15, label: "Konark", count: 45, size: 24 },
];

export default function DistrictMap() {
  const mapRef = useRef(null);
  const instanceRef = useRef(null);

  useEffect(() => {
    if (instanceRef.current) return; // already initialized

    // Dynamically load Leaflet CSS
    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }

    // Load Leaflet JS
    const script = document.createElement("script");
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.onload = () => {
      const L = window.L;
      if (!mapRef.current || instanceRef.current) return;

      const map = L.map(mapRef.current, {
        center: [19.9, 85.8],
        zoom: 9,
        zoomControl: false,
        scrollWheelZoom: false,
        attributionControl: false,
      });

      instanceRef.current = map;

      // OpenStreetMap tiles — completely free
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
      }).addTo(map);

      // Zoom control bottom-right
      L.control.zoom({ position: "bottomright" }).addTo(map);

      // Cluster bubbles
      CLUSTER_POINTS.forEach(({ lat, lng, label, count, size }) => {
        const icon = L.divIcon({
          className: "",
          html: `
            <div style="
              width:${size}px;height:${size}px;
              background:rgba(34,120,60,0.85);
              border:2.5px solid rgba(255,255,255,0.7);
              border-radius:50%;
              display:flex;align-items:center;justify-content:center;
              box-shadow:0 2px 12px rgba(34,120,60,0.45);
              font-family:Poppins,sans-serif;font-size:${size > 38 ? 11 : 9}px;
              font-weight:700;color:#fff;
              animation: pulse-marker 2s infinite;
            ">${count}</div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.addTo(map);
        marker.bindTooltip(`<b>${label}</b><br/>${count} farmers`, {
          direction: "top",
          offset: [0, -(size / 2) - 4],
          className: "leaflet-maatitrace-tooltip",
        });
      });

      // Inject tooltip style
      const style = document.createElement("style");
      style.textContent = `
        .leaflet-maatitrace-tooltip {
          background: rgba(255,255,255,0.97);
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 5px 10px;
          font-family: Poppins, sans-serif;
          font-size: 11px;
          color: #1f2937;
          box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }
        .leaflet-maatitrace-tooltip::before { display: none; }
      `;
      document.head.appendChild(style);
    };
    document.head.appendChild(script);

    return () => {
      if (instanceRef.current) {
        instanceRef.current.remove();
        instanceRef.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={mapRef}
      className="w-full rounded-2xl overflow-hidden"
      style={{ height: "360px" }}
    />
  );
}