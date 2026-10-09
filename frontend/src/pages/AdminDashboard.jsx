import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users, MapPin, AlertTriangle,
  Layers,
  CheckCircle, XCircle, LoaderCircle,
} from "lucide-react";
import { motion } from "framer-motion";
import StatStrip from "@/components/ui-custom/StatStrip";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import FarmPointerMap from "@/components/ui-custom/FarmPointerMap";
import { getFpoFarmers, getFpoFarms, getFpos } from "@/lib/api/fpo";
import { getFarms } from "@/lib/api/farm";

export default function AdminDashboard() {
  const [fpos, setFpos] = useState([]);
  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");
      try {
        const [fpoList, farmList] = await Promise.all([
          getFpos().catch(() => []),
          getFarms().catch(() => []),
        ]);

        const enrichedFpos = await Promise.all(
          (fpoList || []).map(async (fpo) => {
            const [farmers, farms] = await Promise.all([
              getFpoFarmers(fpo.fpo_id).catch(() => []),
              getFpoFarms(fpo.fpo_id).catch(() => []),
            ]);
            return { ...fpo, farmers, farms };
          }),
        );

        if (cancelled) return;
        setFpos(enrichedFpos);
        setFarms(Array.isArray(farmList) ? farmList : []);
      } catch (err) {
        if (cancelled) return;
        setError(typeof err?.message === "string" ? err.message : "Unable to load admin dashboard.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  const totals = useMemo(() => {
    const farmers = fpos.reduce((sum, fpo) => sum + (fpo.farmers?.length || 0), 0);
    const farms = fpos.reduce((sum, fpo) => sum + (fpo.farms?.length || 0), 0);
    const hectares = fpos.reduce(
      (sum, fpo) => sum + (fpo.farms || []).reduce((farmSum, farm) => farmSum + Number(farm.area_acres || 0), 0),
      0,
    );
    return { farmers, farms, hectares };
  }, [fpos]);

  const districts = useMemo(() => {
    const grouped = new Map();
    fpos.forEach((fpo) => {
      const key = fpo.district_name || "Unknown";
      if (!grouped.has(key)) {
        grouped.set(key, { name: key, fpos: 0, farmers: 0, farms: 0, hectares: 0, coverage: 0 });
      }
      const bucket = grouped.get(key);
      bucket.fpos += 1;
      bucket.farmers += fpo.farmers?.length || 0;
      bucket.farms += fpo.farms?.length || 0;
      bucket.hectares += (fpo.farms || []).reduce((sum, farm) => sum + Number(farm.area_acres || 0), 0);
    });
    return Array.from(grouped.values()).map((bucket) => ({
      ...bucket,
      coverage: Math.min(100, Math.round((bucket.farms / Math.max(bucket.farmers, 1)) * 20)),
    }));
  }, [fpos]);

  const recentProcessing = [
    { batch: "Gateway", farms: totals.farms, status: "completed", time: "Available", failed: 0 },
    { batch: "Analytics", farms: totals.farmers, status: "completed", time: "Linked", failed: 0 },
    { batch: "Grid", farms: 0, status: "pending", time: "Endpoint pending", failed: 0 },
    { batch: "Raster", farms: 0, status: "pending", time: "Endpoint pending", failed: 0 },
  ];

  return (
    <div className="min-h-screen bg-[#f8faf9]">
      <main className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Admin Command Center</h1>
          <p className="mt-0.5 text-xs font-medium uppercase tracking-wider text-gray-400">Platform-wide overview - MaatiTrace Operations</p>
        </div>
      </div>

      {loading && (
        <div className="flex min-h-52 flex-col items-center justify-center rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
          <div className="relative flex h-16 w-16 items-center justify-center">
            <motion.div
              className="absolute inset-0 rounded-full border-4 border-emerald-100 border-t-emerald-500"
              animate={{ rotate: 360 }}
              transition={{ duration: 1.1, repeat: Infinity, ease: "linear" }}
            />
            <motion.div
              className="absolute h-7 w-7 rounded-full bg-emerald-50"
              animate={{ scale: [1, 1.22, 1], opacity: [0.65, 1, 0.65] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.div
              className="relative"
              animate={{ rotate: 360 }}
              transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
            >
              <LoaderCircle className="h-5 w-5 text-emerald-600" aria-hidden="true" />
            </motion.div>
          </div>
          <p className="mt-4 text-sm font-bold text-slate-700">Loading admin dashboard</p>
          <p className="mt-1 text-xs text-slate-400">Loading your operational overview...</p>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-rose-100 bg-rose-50 p-6 text-sm text-rose-600 shadow-sm">
          {error}
        </div>
      )}

      <StatStrip items={[
        { label: "Total FPOs", value: fpos.length, icon: Users },
        { label: "Registered Farmers", value: totals.farmers, icon: Users },
        { label: "Total Farms", value: totals.farms, icon: MapPin },
        { label: "Total Area", value: totals.hectares.toFixed(1), unit: "ac", icon: Layers },
        { label: "Pending Jobs", value: 0, icon: AlertTriangle, sub: "No job data" },
      ]} />

      <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
          <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
            <MapPin className="h-4 w-4 text-emerald-500" />
            Farm Pointers
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{farms.length} farms</span>
        </div>
        <div className="p-4">
          <FarmPointerMap
            farms={farms}
            onFarmClick={(farm) => window.location.assign(`/land/${farm.farm_id}`)}
            showBoundaries
            height={420}
            userRole="admin"
            emptyMessage="No accessible farms yet."
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <MapPin className="h-4 w-4 text-blue-500" />
                District Coverage - Odisha
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    {["District", "FPOs", "Farmers", "Farms", "Area", "Coverage"].map((header) => (
                      <th key={header} className="px-4 py-2.5 text-left text-[9px] font-semibold uppercase tracking-wider text-gray-400">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {districts.map((district) => (
                    <tr key={district.name} className="border-b border-gray-50 transition-colors hover:bg-gray-50/60 last:border-0">
                      <td className="px-4 py-2.5 font-bold text-gray-700">{district.name}</td>
                      <td className="px-4 py-2.5 text-gray-600">{district.fpos}</td>
                      <td className="px-4 py-2.5 font-bold text-gray-700">{district.farmers}</td>
                      <td className="px-4 py-2.5 text-gray-600">{district.farms}</td>
                      <td className="px-4 py-2.5 text-gray-600">{district.hectares.toFixed(1)}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-16 overflow-hidden rounded-full bg-gray-100">
                            <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600" style={{ width: `${district.coverage}%` }} />
                          </div>
                          <span className="font-bold text-emerald-600">{district.coverage}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!loading && !error && districts.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-4 py-6 text-center text-sm text-gray-500">
                        District coverage will appear after FPO records are available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <Layers className="h-4 w-4 text-violet-500" />
                Recent Processing
              </span>
            </div>
            <div className="space-y-2 p-4">
              {recentProcessing.map((item) => (
                <div key={item.batch} className="flex items-center justify-between rounded-xl border border-gray-100 p-3 transition-colors hover:bg-gray-50/70">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${item.status === "completed" ? "bg-emerald-50" : "bg-rose-50"}`}>
                      {item.status === "completed"
                        ? <CheckCircle className="h-4 w-4 text-emerald-500" />
                        : <XCircle className="h-4 w-4 text-rose-500" />}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-gray-700">{item.batch}</span>
                      <span className="ml-2 text-[10px] text-gray-400">{item.farms} records</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-gray-400">
                    {item.failed > 0 && <span className="font-medium text-rose-500">{item.failed} failed</span>}
                    <span>{item.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-4 py-3">
              <span className="text-sm font-semibold text-gray-800">FPO Registry</span>
            </div>
            <div className="divide-y divide-gray-50">
              {fpos.map((fpo) => (
                <Link key={fpo.fpo_id} to={`/fpo/${fpo.fpo_id}`} className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-gray-50">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{fpo.fpo_name}</p>
                    <p className="text-xs text-gray-500">{fpo.district_name}, {fpo.state_name}</p>
                  </div>
                  <div className="text-right text-xs text-gray-500">
                    <p>{fpo.farmers?.length || 0} farmers</p>
                    <p>{fpo.farms?.length || 0} farms</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-4 py-3">
              <span className="text-sm font-semibold text-gray-800">System Management</span>
            </div>
            <div className="divide-y divide-gray-50">
              <Link to="/admin/fpo" className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-gray-50">
                <div><p className="text-sm font-semibold text-gray-800">FPO Management</p><p className="text-xs text-gray-500">Verification, provisioning, and FPO configuration</p></div>
                <p className="text-xs font-bold text-emerald-600">Open</p>
              </Link>
              <Link to="/admin/system" className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-gray-50">
                <p className="text-sm font-semibold text-gray-800">Feature Engine &amp; pipelines</p>
                <p className="text-xs text-gray-500">Crop profiles, formulas, raster, analytics, hot stream</p>
              </Link>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-4 py-3">
              <span className="text-sm font-semibold text-gray-800">Crop Observations</span>
            </div>
            <div className="divide-y divide-gray-50">
              <Link to="/admin/crop-observation" className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-gray-50">
                <p className="text-sm font-semibold text-gray-800">Crop Observation</p>
                <p className="text-xs text-gray-500">Records, issues, configuration, media and system status</p>
              </Link>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                System Alerts
              </span>
              <span className="pulse-live h-2 w-2 rounded-full bg-rose-400" />
            </div>
            <div className="p-2">
              <NotificationStack limit={5} />
            </div>
          </div>
        </div>
      </div>
      </main>
    </div>
  );
}
