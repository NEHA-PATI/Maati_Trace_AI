import React, { useMemo } from "react";
import { MapContainer, Marker, Polygon, TileLayer, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

function normalizeRing(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return geometry.coordinates?.[0] || [];
  if (geometry.type === "MultiPolygon") return geometry.coordinates?.[0]?.[0] || [];
  return [];
}

function centroidFromPolygon(polygonGeoJson, bbox) {
  const ring = normalizeRing(polygonGeoJson);
  if (ring.length) {
    const [sumLon, sumLat] = ring.reduce((acc, [lon, lat]) => [acc[0] + lon, acc[1] + lat], [0, 0]);
    return [sumLat / ring.length, sumLon / ring.length];
  }
  if (Array.isArray(bbox) && bbox.length === 4) {
    return [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2];
  }
  return [20.2961, 85.8245];
}

function boundsFromFarms(farms) {
  const points = [];
  farms.forEach((farm) => {
    const ring = normalizeRing(farm.polygon_geojson);
    if (ring.length) {
      ring.forEach(([lon, lat]) => points.push([lat, lon]));
      return;
    }
    if (Array.isArray(farm.bbox) && farm.bbox.length === 4) {
      points.push([farm.bbox[1], farm.bbox[0]]);
      points.push([farm.bbox[3], farm.bbox[2]]);
    }
  });
  if (!points.length) return null;
  const lats = points.map(([lat]) => lat);
  const lons = points.map(([, lon]) => lon);
  return [
    [Math.min(...lats), Math.min(...lons)],
    [Math.max(...lats), Math.max(...lons)],
  ];
}

function colorForFarm(farm) {
  const stress = farm.health_status === "degrading" || Number(farm.latest_bsi) > 0.15;
  if (stress) return "#ef4444";
  if (farm.health_status === "stable") return "#10b981";
  return "#3b82f6";
}

function FitBounds({ bounds }) {
  const map = useMap();
  React.useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [24, 24], animate: true, duration: 0.75 });
    }
  }, [bounds, map]);
  return null;
}

export default function FarmPointerMap({
  farms = [],
  selectedFarmId = null,
  onFarmClick,
  showBoundaries = false,
  showGridForSelected = false,
  height = 520,
  userRole,
  emptyMessage = "No farms available yet.",
}) {
  const bounds = useMemo(() => boundsFromFarms(farms), [farms]);
  const selectedFarm = useMemo(() => farms.find((farm) => String(farm.farm_id) === String(selectedFarmId)) || null, [farms, selectedFarmId]);

  const defaultCenter = selectedFarm
    ? centroidFromPolygon(selectedFarm.polygon_geojson, selectedFarm.bbox)
    : farms[0]
      ? centroidFromPolygon(farms[0].polygon_geojson, farms[0].bbox)
      : [20.2961, 85.8245];

  const getFarmIcon = (farm) => L.divIcon({
    className: "maatitrace-farm-pointer",
    html: `<div style="width:16px;height:16px;border-radius:999px;background:${colorForFarm(farm)};box-shadow:0 0 0 4px rgba(255,255,255,.55),0 6px 16px rgba(0,0,0,.25);border:2px solid white;transition:transform .2s ease;"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

  return (
    <div className="relative overflow-hidden rounded-3xl border border-gray-200 shadow-xl" style={{ height }}>
      <MapContainer
        center={defaultCenter}
        zoom={16}
        className="h-full w-full"
        scrollWheelZoom
        zoomControl
        attributionControl={false}
      >
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution='Tiles &copy; Esri'
          maxZoom={19}
        />
        {bounds && <FitBounds bounds={bounds} />}
        {farms.map((farm) => {
          const ring = normalizeRing(farm.polygon_geojson);
          const centroid = centroidFromPolygon(farm.polygon_geojson, farm.bbox);
          const selected = String(farm.farm_id) === String(selectedFarmId);
          return (
            <React.Fragment key={farm.farm_id}>
              <Marker
                position={centroid}
                icon={getFarmIcon(farm)}
                eventHandlers={{ click: () => onFarmClick?.(farm) }}
              >
                <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent={false}>
                  <div className="space-y-1 text-[11px] text-slate-900">
                    <div className="font-bold">{farm.farm_name || "Farm"}</div>
                    <div>{[farm.village_name, farm.block_name, farm.district_name].filter(Boolean).join(" · ") || "Location pending"}</div>
                    <div>{farm.area_acres ? `${Number(farm.area_acres).toFixed(2)} ac` : "Area pending"}</div>
                    <div>{farm.latest_ndvi !== undefined && farm.latest_ndvi !== null ? `NDVI ${Number(farm.latest_ndvi).toFixed(3)}` : "NDVI unavailable"}</div>
                  </div>
                </Tooltip>
              </Marker>
              {(showBoundaries || selected) && ring.length >= 3 && (
                <Polygon
                  positions={ring.map(([lon, lat]) => [lat, lon])}
                  pathOptions={{
                    color: selected ? "#f59e0b" : "#ef4444",
                    weight: selected ? 3 : 2,
                    fillOpacity: selected ? 0.18 : 0.08,
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>
      {farms.length === 0 && (
        <div className="pointer-events-none absolute left-4 top-4 rounded-2xl bg-black/55 px-3 py-2 text-xs text-white backdrop-blur">
          {emptyMessage}
        </div>
      )}
    </div>
  );
}
