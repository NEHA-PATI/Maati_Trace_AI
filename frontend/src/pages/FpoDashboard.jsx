import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  Users, MapPin, Hexagon, BarChart3, FileUp, Plus,
  ChevronRight, AlertTriangle,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import FarmPointerMap from "@/components/ui-custom/FarmPointerMap";
import {
  getFpo,
  getFpoFarmers,
  getFpoFarms,
  getFpoSummary,
  getMyFpo,
} from "@/lib/api/fpo";

export default function FpoDashboard() {
  const { fpoId } = useParams();
  const location = useLocation();
  const isSelfRoute = location.pathname === "/fpo/me";

  const [fpo, setFpo] = useState(null);
  const [summary, setSummary] = useState(null);
  const [farmers, setFarmers] = useState([]);
  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");
      try {
        const baseFpo = isSelfRoute ? await getMyFpo() : await getFpo(fpoId);
        const [summaryPayload, farmersPayload, farmsPayload] = await Promise.all([
          getFpoSummary(baseFpo.fpo_id).catch(() => null),
          getFpoFarmers(baseFpo.fpo_id).catch(() => []),
          getFpoFarms(baseFpo.fpo_id).catch(() => []),
        ]);

        if (cancelled) return;
        setFpo(baseFpo);
        setSummary(summaryPayload);
        setFarmers(farmersPayload || []);
        setFarms(farmsPayload || []);
      } catch (err) {
        if (cancelled) return;
        setError(typeof err?.message === "string" ? err.message : "Unable to load FPO dashboard.");
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
  }, [fpoId, isSelfRoute]);

  const farmerRows = useMemo(() => (
    (farmers || []).map((farmer) => {
      const farmerFarms = farms.filter((farm) => farm.farmer_id === farmer.farmer_id);
      const hectares = farmerFarms.reduce((sum, farm) => sum + Number(farm.area_acres || 0), 0);
      return {
        id: farmer.farmer_id,
        name: farmer.full_name || "Unnamed farmer",
        village: farmer.village_name || "Village unavailable",
        block: farmer.block_name || "Block unavailable",
        farms: farmerFarms.length,
        hectares,
        status: farmer.is_active ? "active" : "pending",
      };
    })
  ), [farmers, farms]);

  const blockCoverage = useMemo(() => {
    const grouped = new Map();
    farmerRows.forEach((row) => {
      const key = row.block || "Unmapped";
      if (!grouped.has(key)) {
        grouped.set(key, { block: key, farmers: 0, farms: 0, hectares: 0, coverage: 0 });
      }
      const bucket = grouped.get(key);
      bucket.farmers += 1;
      bucket.farms += row.farms;
      bucket.hectares += row.hectares;
    });
    return Array.from(grouped.values()).map((bucket) => ({
      ...bucket,
      coverage: Math.min(100, Math.round((bucket.farms / Math.max(bucket.farmers, 1)) * 20)),
    }));
  }, [farmerRows]);

  const totalArea = useMemo(
    () => farms.reduce((sum, farm) => sum + Number(farm.area_acres || 0), 0),
    [farms],
  );

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold text-gray-800">FPO Command Center</h1>
          <p className="mt-0.5 text-xs font-medium uppercase tracking-wider text-gray-400">
            {fpo ? `${fpo.fpo_name} - ${fpo.district_name}, ${fpo.state_name}` : "Farmer Producer Organisation"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/farm-register">
            <Button size="sm" className="h-9 rounded-xl bg-emerald-600 text-xs font-semibold hover:bg-emerald-700">
              <Plus className="mr-1 h-3.5 w-3.5" />
              Register Farm
            </Button>
          </Link>
          <Link to="/bulk-upload">
            <Button size="sm" variant="outline" className="h-9 rounded-xl border-gray-200 text-xs font-semibold hover:bg-gray-50">
              <FileUp className="mr-1 h-3.5 w-3.5 text-amber-500" />
              Bulk Upload
            </Button>
          </Link>
        </div>
      </div>

      {loading && (
        <div className="rounded-2xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">
          Loading FPO dashboard...
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-rose-100 bg-rose-50 p-6 text-sm text-rose-600 shadow-sm">
          {error}
        </div>
      )}

      <StatStrip items={[
        { label: "Registered Farmers", value: farmerRows.length, icon: Users },
        { label: "Total Farms", value: farms.length, icon: MapPin },
        { label: "Total Area", value: totalArea.toFixed(1), unit: "ac", icon: Hexagon },
        { label: "Active Blocks", value: blockCoverage.length, icon: Hexagon },
        { label: "Pending Actions", value: Math.max(0, farmerRows.filter((item) => item.status !== "active").length), icon: AlertTriangle },
      ]} />

      <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">System Pipeline Status</span>
          <VerificationStamp label="OPERATIONAL" type="success" compact />
        </div>
        <PipelineStepper
          steps={["Location", "Farmer", "Boundary", "H3 Grid", "Satellite", "Raster", "Intelligence"]}
          currentStep={summary ? 7 : 5}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <MapPin className="h-4 w-4 text-emerald-500" />
                Farm Pointers
              </span>
              <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">{farms.length} farms</span>
            </div>
            <div className="p-3">
              <FarmPointerMap
                farms={farms}
                selectedFarmId={null}
                onFarmClick={(farm) => window.location.assign(`/land/${farm.farm_id}`)}
                showBoundaries={false}
                height={420}
                userRole="fpo"
                emptyMessage="No farms are linked to this FPO yet."
              />
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <Users className="h-4 w-4 text-blue-500" />
                Recent Farmer Registrations
              </span>
              <Link to="/my-fpo" className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-600 hover:underline">
                View All
                <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">Farmer ID</th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">Name</th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">Village</th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">Block</th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-400">Farms</th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-400">Area</th>
                    <th className="px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-gray-400">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {farmerRows.map((row) => (
                    <tr key={row.id} className="border-b border-gray-50 last:border-0 transition-colors hover:bg-gray-50/60">
                      <td className="px-4 py-2.5 font-bold text-gray-700">{row.id}</td>
                      <td className="px-4 py-2.5">
                        <Link to={`/farmers/${row.id}`} className="font-medium text-emerald-600 hover:underline">{row.name}</Link>
                      </td>
                      <td className="px-4 py-2.5 text-gray-500">{row.village}</td>
                      <td className="px-4 py-2.5 text-gray-500">{row.block}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">{row.farms}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">{row.hectares.toFixed(1)}</td>
                      <td className="px-4 py-2.5 text-center">
                        <VerificationStamp label={row.status.toUpperCase()} type={row.status === "active" ? "success" : "pending"} compact />
                      </td>
                    </tr>
                  ))}
                  {!loading && !error && farmerRows.length === 0 && (
                    <tr>
                      <td colSpan="7" className="px-4 py-6 text-center text-sm text-gray-500">
                        No farmers are linked to this FPO yet.
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
                <BarChart3 className="h-4 w-4 text-violet-500" />
                Block-wise Coverage
              </span>
            </div>
            <div className="space-y-4 p-5">
              {blockCoverage.map((block) => (
                <div key={block.block} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-gray-700">{block.block}</span>
                    <div className="flex items-center gap-3 text-[10px] font-medium text-gray-400">
                      <span>{block.farmers} farmers</span>
                      <span>{block.farms} farms</span>
                      <span className="font-bold text-emerald-600">{block.coverage}%</span>
                    </div>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${block.coverage}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, delay: 0.1 }}
                      className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                    />
                  </div>
                </div>
              ))}
              {!loading && !error && blockCoverage.length === 0 && (
                <div className="text-sm text-gray-500">Block coverage will appear once farmer and farm records are available.</div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                Alerts
              </span>
              <span className="pulse-live h-2 w-2 rounded-full bg-rose-400" />
            </div>
            <div className="p-2">
              <NotificationStack limit={5} />
            </div>
          </div>

          <div className="space-y-1 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">Quick Actions</span>
            <Link to="/farm-register" className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-gray-50">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50">
                <MapPin className="h-4 w-4 text-emerald-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">Register New Farm</p>
                <p className="text-[10px] text-gray-400">Individual boundary registration</p>
              </div>
              <ChevronRight className="ml-auto h-3.5 w-3.5 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
            <Link to="/bulk-upload" className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-gray-50">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50">
                <FileUp className="h-4 w-4 text-amber-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">Bulk CSV Upload</p>
                <p className="text-[10px] text-gray-400">Register multiple farms at once</p>
              </div>
              <ChevronRight className="ml-auto h-3.5 w-3.5 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
            <Link to="/my-fpo" className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-gray-50">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50">
                <Users className="h-4 w-4 text-blue-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">View All Farmers</p>
                <p className="text-[10px] text-gray-400">Map view with population density</p>
              </div>
              <ChevronRight className="ml-auto h-3.5 w-3.5 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">FPO Identity</span>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between"><span className="font-medium text-gray-400">FPO ID</span><span className="font-bold text-gray-700">{fpo?.fpo_id || "Pending"}</span></div>
              <div className="flex justify-between"><span className="font-medium text-gray-400">Region</span><span className="text-gray-700">{fpo ? `${fpo.district_name}, ${fpo.state_name}` : "Pending"}</span></div>
              <div className="flex justify-between"><span className="font-medium text-gray-400">Block</span><span className="text-gray-700">{fpo?.block_name || "Multi-block"}</span></div>
              <div className="flex items-center justify-between"><span className="font-medium text-gray-400">Status</span><VerificationStamp label={fpo?.is_active ? "ACTIVE" : "PENDING"} type={fpo?.is_active ? "success" : "pending"} compact /></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
