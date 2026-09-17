import { createElement, useCallback, useMemo, useRef, useState } from "react";
import { Circle, MapContainer, ZoomControl } from "react-leaflet";
import { LocateFixed, MousePointer2, Move, Pencil, RotateCcw, Trash2 } from "lucide-react";
import "leaflet/dist/leaflet.css";
import { MAP_CONFIG } from "@/lib/mapConfig";
import EsriBasemap from "./EsriBasemap";
import MapCamera from "./MapCamera";
import BoundaryDrawingController from "./BoundaryDrawingController";
import { calculateBoundarySummary, geoJsonBounds } from "./boundaryUtils";
import useDeviceLocation from "./useDeviceLocation";

function MapAction({ label, icon: Icon, className = "", ...props }) {
  return (
    <button type="button" aria-label={label} title={label} className={`group relative flex h-11 items-center justify-center rounded-xl border px-3 transition-all hover:-translate-y-0.5 hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-40 ${className}`} {...props}>
      {createElement(Icon, { className: "h-5 w-5", strokeWidth: 2.2 })}
      <span className="pointer-events-none absolute bottom-[calc(100%+8px)] left-1/2 z-[700] hidden -translate-x-1/2 whitespace-nowrap rounded-lg bg-slate-900 px-2.5 py-1.5 text-[11px] font-semibold text-white shadow-lg group-hover:block group-focus-visible:block">{label}</span>
    </button>
  );
}

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

      <div className="absolute bottom-5 left-3 right-3 z-[500] md:left-1/2 md:max-w-2xl md:-translate-x-1/2">
        {(mapMessage || gps.error) ? <div className="mb-2 rounded-xl bg-slate-950/90 px-4 py-3 text-sm text-white">{mapMessage || gps.error}</div> : null}
        <div className="rounded-2xl bg-white/95 p-3 shadow-xl backdrop-blur">
          <div className="mb-4 flex items-center justify-between gap-3 border-b border-slate-200/80 pb-4">
            <div>
              <p className="text-xs text-slate-500">Selected farm area</p>
              <p className="text-lg font-bold text-slate-900">{summary.valid ? `${summary.acres.toFixed(2)} acre` : "Not completed"}</p>
              {summary.valid ? <p className="text-xs text-slate-500">{summary.hectares.toFixed(3)} hectare · {summary.pointCount} corners</p> : null}
            </div>
            <button type="button" onClick={gps.locate} disabled={gps.loading} className="h-11 rounded-xl border border-blue-200 bg-blue-50 px-4 text-sm font-semibold text-blue-700">{gps.loading ? "Locating…" : "My location"}</button>
          </div>
          <button type="button" onClick={onConfirm} disabled={!summary.valid} className="mt-2 h-12 w-full rounded-xl bg-emerald-700 px-3 text-sm font-bold text-white disabled:bg-slate-300 md:hidden">Finish boundary</button>
        </div>
      </div>

      <div className="absolute bottom-24 right-3 z-[600] flex flex-col gap-2 rounded-2xl bg-white p-2 shadow-xl ring-1 ring-slate-200/80">
        <MapAction label={drawing ? "Drawing mode active" : "Start drawing"} icon={MousePointer2} onClick={() => issueCommand("start-drawing")} aria-pressed={drawing} className={`text-white ${drawing ? "border-emerald-700 bg-emerald-700 ring-2 ring-emerald-300" : "border-emerald-500 bg-emerald-500"}`} />
        <MapAction label="Undo" icon={RotateCcw} onClick={undo} disabled={!historyRef.current.length} className="border-slate-200 text-slate-600" />
        <MapAction label="Edit corners" icon={Pencil} onClick={() => issueCommand("edit")} disabled={!summary.valid} className="border-emerald-200 text-emerald-700" />
        <MapAction label="Move map" icon={Move} onClick={() => issueCommand("stop-editing")} className="border-slate-200 text-slate-700" />
        <MapAction label="Clear boundary" icon={Trash2} onClick={() => issueCommand("clear")} disabled={!geometry} className="border-rose-200 text-rose-600" />
      </div>
    </div>
  );
}
