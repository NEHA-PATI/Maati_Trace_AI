import { useCallback, useMemo, useRef, useState } from "react";
import { Circle, MapContainer, ZoomControl } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { MAP_CONFIG } from "@/lib/mapConfig";
import EsriBasemap from "./EsriBasemap";
import MapCamera from "./MapCamera";
import BoundaryDrawingController from "./BoundaryDrawingController";
import { calculateBoundarySummary, geoJsonBounds } from "./boundaryUtils";
import useDeviceLocation from "./useDeviceLocation";

export default function FarmMap({ geometry, onGeometryChange, resolvedLocation, onConfirm }) {
  const [command, setCommand] = useState(null);
  const [drawing, setDrawing] = useState(false);
  const [mapMessage, setMapMessage] = useState(MAP_CONFIG.apiKey ? "" : "Satellite imagery is unavailable until the ArcGIS key is configured.");
  const historyRef = useRef([]);
  const lastGeometryRef = useRef(geometry);
  const gps = useDeviceLocation();
  const summary = useMemo(() => calculateBoundarySummary(geometry), [geometry]);
  const polygonBounds = useMemo(() => geoJsonBounds(geometry), [geometry]);
  const cameraTarget = gps.location || resolvedLocation;

  function issueCommand(type, payload = {}) { setCommand({ type, ...payload, id: crypto.randomUUID() }); }
  const handleGeometryChange = useCallback((nextGeometry) => {
    const previous = lastGeometryRef.current;
    if (JSON.stringify(previous) !== JSON.stringify(nextGeometry) && previous) {
      historyRef.current = [...historyRef.current.slice(-19), previous];
    }
    lastGeometryRef.current = nextGeometry;
    onGeometryChange(nextGeometry);
    setMapMessage("");
  }, [onGeometryChange]);
  function undo() {
    const previous = historyRef.current.pop();
    if (!previous) return;
    lastGeometryRef.current = previous;
    onGeometryChange(previous);
    issueCommand("replace", { geometry: previous });
  }

  return (
    <div className="relative">
      <div className="h-[calc(100dvh-175px)] min-h-[500px] overflow-hidden bg-slate-100 md:h-[68vh] md:min-h-[600px] md:rounded-3xl">
        <MapContainer center={[MAP_CONFIG.defaultCenter.lat, MAP_CONFIG.defaultCenter.lng]} zoom={MAP_CONFIG.zoom.default} maxZoom={MAP_CONFIG.zoom.maximum} zoomControl={false} attributionControl className="h-full w-full">
          <EsriBasemap onError={setMapMessage} />
          <ZoomControl position="bottomright" />
          <MapCamera target={cameraTarget} bounds={resolvedLocation?.extent ? [[resolvedLocation.extent.ymin, resolvedLocation.extent.xmin], [resolvedLocation.extent.ymax, resolvedLocation.extent.xmax]] : null} polygonBounds={geometry ? polygonBounds : null} />
          <BoundaryDrawingController geometry={geometry} command={command} onGeometryChange={handleGeometryChange} onDrawingChange={setDrawing} onError={setMapMessage} />
          {gps.location ? <Circle center={[gps.location.latitude, gps.location.longitude]} radius={Math.max(gps.location.accuracy, 3)} pathOptions={{ color: "#2563eb", fillColor: "#60a5fa", fillOpacity: 0.17, weight: 2 }} /> : null}
        </MapContainer>
      </div>

      <div className="absolute left-3 right-3 top-3 z-[500] md:left-4 md:right-auto">
        <div className="rounded-2xl bg-white/95 p-3 shadow-lg backdrop-blur">
          <p className="text-xs font-bold text-slate-900">{drawing ? "Tap every corner of your farm" : "Find your farm in the satellite image"}</p>
          <p className="mt-0.5 text-[11px] text-slate-600">{resolvedLocation?.address || "Use your current location or move the map."}</p>
        </div>
      </div>

      <div className="absolute bottom-3 left-3 right-3 z-[500] md:left-1/2 md:max-w-2xl md:-translate-x-1/2">
        {(mapMessage || gps.error) ? <div className="mb-2 rounded-xl bg-slate-950/90 px-4 py-3 text-sm text-white">{mapMessage || gps.error}</div> : null}
        <div className="rounded-2xl bg-white/95 p-3 shadow-xl backdrop-blur">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs text-slate-500">Selected farm area</p>
              <p className="text-lg font-bold text-slate-900">{summary.valid ? `${summary.acres.toFixed(2)} acre` : "Not completed"}</p>
              {summary.valid ? <p className="text-xs text-slate-500">{summary.hectares.toFixed(3)} hectare · {summary.pointCount} corners</p> : null}
            </div>
            <button type="button" onClick={gps.locate} disabled={gps.loading} className="h-11 rounded-xl border border-blue-200 bg-blue-50 px-4 text-sm font-semibold text-blue-700">{gps.loading ? "Locating…" : "My location"}</button>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            <button type="button" onClick={() => issueCommand("start-drawing")} aria-pressed={drawing} className={`h-11 rounded-xl px-3 text-sm font-bold text-white ${drawing ? "bg-emerald-700 ring-2 ring-emerald-300" : "bg-emerald-500"}`}>{drawing ? "Drawing mode active" : "Start drawing"}</button>
            <button type="button" onClick={undo} disabled={!historyRef.current.length} className="h-11 rounded-xl border border-slate-200 px-3 text-sm font-semibold disabled:opacity-40">Undo</button>
            <button type="button" onClick={() => issueCommand("edit")} disabled={!summary.valid} className="h-11 rounded-xl border border-emerald-200 px-3 text-sm font-semibold text-emerald-700 disabled:opacity-40">Edit corners</button>
            <button type="button" onClick={() => issueCommand("stop-editing")} className="h-11 rounded-xl border border-slate-200 px-3 text-sm font-semibold">Move map</button>
            <button type="button" onClick={() => issueCommand("clear")} disabled={!geometry} className="h-11 rounded-xl border border-rose-200 px-3 text-sm font-semibold text-rose-600 disabled:opacity-40">Clear</button>
          </div>
          <button type="button" onClick={onConfirm} disabled={!summary.valid} className="mt-2 h-12 w-full rounded-xl bg-emerald-700 px-3 text-sm font-bold text-white disabled:bg-slate-300 md:hidden">Finish boundary</button>
        </div>
      </div>
    </div>
  );
}
