import { useEffect, useMemo, useState } from "react";
import { MapContainer, Polygon, TileLayer, Tooltip, useMap } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";

function ringOf(farm) {
  let geometry = farm?.polygon_geojson;
  if (typeof geometry === "string") {
    try { geometry = JSON.parse(geometry); } catch { return []; }
  }
  const ring = geometry?.type === "Polygon" ? geometry.coordinates?.[0] : geometry?.coordinates?.[0]?.[0];
  return (ring || []).filter((point) => Array.isArray(point) && point.length >= 2 && Number.isFinite(Number(point[0])) && Number.isFinite(Number(point[1]))).map(([lon, lat]) => [Number(lat), Number(lon)]);
}

function FitAll({ bounds }) {
  const map = useMap();
  useEffect(() => { if (bounds.length) map.fitBounds(bounds, { padding: [28, 28], animate: false }); }, [bounds, map]);
  return null;
}

export default function FpoFarmPortfolioMap({ farms = [] }) {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState(null);
  const shapes = useMemo(() => farms.map((farm) => ({ farm, ring: ringOf(farm) })).filter(({ ring }) => ring.length >= 3), [farms]);
  const bounds = useMemo(() => shapes.flatMap(({ ring }) => ring), [shapes]);
  const center = useMemo(() => bounds[0] || [20.3, 85.8], [bounds]);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200">
      <MapContainer center={center} zoom={13} className="h-[460px] w-full" scrollWheelZoom zoomControl attributionControl={false}>
        <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" attribution="Tiles © Esri" maxZoom={19} />
        <FitAll bounds={bounds} />
        {shapes.map(({ farm, ring }) => (
          <Polygon
            key={farm.farm_id}
            positions={ring}
            bubblingMouseEvents={false}
            pathOptions={{ color: hovered === farm.farm_id ? "#064e3b" : "#10b981", weight: hovered === farm.farm_id ? 5 : 2, fillColor: "#34d399", fillOpacity: hovered === farm.farm_id ? 0.42 : 0.2 }}
            eventHandlers={{
              mouseover: () => setHovered(farm.farm_id),
              mouseout: () => setHovered(null),
              click: (event) => { event.originalEvent?.stopPropagation(); navigate(`/fpo/farmers/${farm.farmer_id}/farms/${farm.farm_id}/intelligence`); },
            }}
          >
            <Tooltip sticky><span className="font-semibold">{farm.farm_name || "Unnamed farm"}</span><br />{farm.farmer_name || "Farmer"}<br />Click to open intelligence</Tooltip>
          </Polygon>
        ))}
      </MapContainer>
      {!shapes.length && <div className="absolute inset-0 grid place-items-center bg-slate-50/90 text-sm text-slate-500">Farm boundaries are not available yet.</div>}
      <div className="pointer-events-none absolute left-3 top-3 rounded-xl bg-white/95 px-3 py-2 text-xs font-semibold text-slate-700 shadow">{shapes.length} farm boundaries · hover to inspect · click to open</div>
    </div>
  );
}
