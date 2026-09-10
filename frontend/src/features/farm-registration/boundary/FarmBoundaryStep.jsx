import { useMemo } from "react";
import FarmMap from "./FarmMap";
import { calculateBoundarySummary } from "./boundaryUtils";

export default function FarmBoundaryStep({ geometry, onGeometryChange, resolvedLocation, locationLabel, onChangeLocation, onConfirm }) {
  const summary = useMemo(() => calculateBoundarySummary(geometry), [geometry]);
  return (
    <div className="md:grid md:grid-cols-[minmax(0,1fr)_320px] md:gap-5">
      <div className="overflow-hidden md:rounded-3xl"><FarmMap geometry={geometry} onGeometryChange={onGeometryChange} resolvedLocation={resolvedLocation} onConfirm={onConfirm} /></div>
      <aside className="hidden space-y-4 rounded-3xl border border-slate-200 bg-white p-5 md:block">
        <div><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Selected location</p><p className="mt-1 text-sm font-semibold text-slate-900">{locationLabel || "Location pending"}</p><button type="button" onClick={onChangeLocation} className="mt-2 text-sm font-semibold text-emerald-700">Change location</button></div>
        <div className="rounded-2xl bg-emerald-50 p-4"><p className="text-sm font-bold text-emerald-900">How to mark the farm</p><ol className="mt-2 space-y-2 text-sm text-emerald-800"><li>1. Find the farm in the satellite image.</li><li>2. Zoom until field edges are visible.</li><li>3. Select Start drawing.</li><li>4. Select every corner.</li><li>5. Finish and correct the corners.</li></ol></div>
        <div className="rounded-2xl border border-slate-200 p-4"><p className="text-xs text-slate-500">Boundary status</p><p className={`mt-1 font-bold ${summary.valid ? "text-emerald-700" : "text-amber-700"}`}>{summary.message}</p>{summary.valid ? <div className="mt-3 space-y-1 text-sm"><p>{summary.acres.toFixed(2)} acre</p><p>{summary.hectares.toFixed(3)} hectare</p><p>{summary.pointCount} boundary corners</p></div> : null}</div>
        <button type="button" disabled={!summary.valid} onClick={onConfirm} className="h-12 w-full rounded-2xl bg-emerald-500 text-sm font-bold text-white disabled:bg-slate-300">Confirm this boundary</button>
        <p className="text-xs leading-5 text-slate-500">This selected boundary is used for farm analysis. It is not an official government land survey.</p>
      </aside>
    </div>
  );
}
