import React, { useState } from "react";
import { Link } from "react-router-dom";
import { 
  Users, MapPin, Hexagon, BarChart3, FileUp, Plus, 
  ChevronRight, Wheat, Layers, AlertTriangle, TrendingUp
} from "lucide-react";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import DistrictMap from "@/components/ui-custom/DistrictMap";
import { motion } from "framer-motion";

const DEMO_FARMERS = [
  { id: "FR-001", name: "Ramesh Sahoo", village: "Baliguali", block: "Puri Sadar", farms: 3, hectares: 7.2, status: "active" },
  { id: "FR-002", name: "Sita Behera", village: "Chandanpur", block: "Nayagarh", farms: 2, hectares: 4.8, status: "active" },
  { id: "FR-003", name: "Mohan Pradhan", village: "Konark", block: "Puri Sadar", farms: 1, hectares: 2.1, status: "pending" },
  { id: "FR-004", name: "Lakshmi Das", village: "Pipili", block: "Delang", farms: 4, hectares: 9.6, status: "active" },
  { id: "FR-005", name: "Bijay Naik", village: "Nimapara", block: "Nimapara", farms: 2, hectares: 5.3, status: "active" },
];

const BLOCKS_COVERAGE = [
  { block: "Puri Sadar", farmers: 142, farms: 312, hectares: 856.4, coverage: 78 },
  { block: "Nayagarh", farmers: 89, farms: 198, hectares: 534.2, coverage: 62 },
  { block: "Delang", farmers: 67, farms: 145, hectares: 398.7, coverage: 55 },
  { block: "Nimapara", farmers: 104, farms: 234, hectares: 612.8, coverage: 71 },
  { block: "Konark", farmers: 45, farms: 89, hectares: 245.3, coverage: 38 },
];

export default function FpoDashboard() {
  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">FPO Command Center</h1>
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-0.5">Odisha Farmer Producer Organisation — Puri District Cluster</p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/farm-register">
            <Button size="sm" className="h-9 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-700">
              <Plus className="w-3.5 h-3.5 mr-1" />Register Farm
            </Button>
          </Link>
          <Link to="/bulk-upload">
            <Button size="sm" variant="outline" className="h-9 text-xs font-semibold rounded-xl border-gray-200 hover:bg-gray-50">
              <FileUp className="w-3.5 h-3.5 mr-1 text-amber-500" />Bulk Upload
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Strip */}
      <StatStrip items={[
        { label: "Registered Farmers", value: "447", icon: Users },
        { label: "Total Farms", value: "978", icon: MapPin },
        { label: "Total Hectares", value: "2,647", unit: "ha", icon: Layers },
        { label: "Active Blocks", value: "12", icon: Hexagon },
        { label: "Pending Actions", value: "23", icon: AlertTriangle, sub: "7 priority" },
      ]} />

      {/* Pipeline status */}
      <div className="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">System Pipeline Status</span>
          <VerificationStamp label="OPERATIONAL" type="success" compact />
        </div>
        <PipelineStepper 
          steps={["Location", "Farmer", "Boundary", "H3 Grid", "Satellite", "Raster", "Intelligence"]}
          currentStep={7}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content — Map + Farmers */}
        <div className="lg:col-span-2 space-y-6">
          {/* Real Leaflet Map */}
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-500" />
                District Coverage Map
              </span>
              <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">Odisha — Puri District</span>
            </div>
            <div className="p-3">
              <DistrictMap />
            </div>
          </div>

          {/* Recent Farmers Table */}
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-500" />Recent Farmer Registrations
              </span>
              <Link to="/my-fpo" className="text-[10px] font-semibold uppercase tracking-wider text-emerald-600 hover:underline flex items-center gap-1">
                View All <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    <th className="text-left px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Farmer ID</th>
                    <th className="text-left px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Name</th>
                    <th className="text-left px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Village</th>
                    <th className="text-left px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Block</th>
                    <th className="text-right px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Farms</th>
                    <th className="text-right px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Hectares</th>
                    <th className="text-center px-4 py-2.5 font-semibold uppercase tracking-wider text-[10px] text-gray-400">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {DEMO_FARMERS.map((f) => (
                    <tr key={f.id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors">
                      <td className="px-4 py-2.5 font-bold text-gray-700">{f.id}</td>
                      <td className="px-4 py-2.5">
                        <Link to={`/farmer-profile/${f.id}`} className="text-emerald-600 hover:underline font-medium">{f.name}</Link>
                      </td>
                      <td className="px-4 py-2.5 text-gray-500">{f.village}</td>
                      <td className="px-4 py-2.5 text-gray-500">{f.block}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">{f.farms}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">{f.hectares}</td>
                      <td className="px-4 py-2.5 text-center">
                        <VerificationStamp label={f.status.toUpperCase()} type={f.status === "active" ? "success" : "pending"} compact />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Block Coverage */}
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-violet-500" />Block-wise Coverage
              </span>
            </div>
            <div className="p-5 space-y-4">
              {BLOCKS_COVERAGE.map((b) => (
                <div key={b.block} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-gray-700">{b.block}</span>
                    <div className="flex items-center gap-3 text-gray-400 text-[10px] font-medium">
                      <span>{b.farmers} farmers</span>
                      <span>{b.farms} farms</span>
                      <span className="font-bold text-emerald-600">{b.coverage}%</span>
                    </div>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${b.coverage}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, delay: 0.1 }}
                      className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right panel — Notifications */}
        <div className="space-y-5">
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />Alerts
              </span>
              <span className="w-2 h-2 bg-rose-400 rounded-full pulse-live" />
            </div>
            <div className="p-2">
              <NotificationStack limit={5} />
            </div>
          </div>

          {/* Quick actions */}
          <div className="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm space-y-1">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400 block mb-3">Quick Actions</span>
            <Link to="/farm-register" className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-50 transition-colors group">
              <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-emerald-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">Register New Farm</p>
                <p className="text-[10px] text-gray-400">Individual boundary registration</p>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-gray-300 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            <Link to="/bulk-upload" className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-50 transition-colors group">
              <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center">
                <FileUp className="w-4 h-4 text-amber-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">Bulk CSV Upload</p>
                <p className="text-[10px] text-gray-400">Register multiple farms at once</p>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-gray-300 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            <Link to="/my-fpo" className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-50 transition-colors group">
              <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
                <Users className="w-4 h-4 text-blue-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">View All Farmers</p>
                <p className="text-[10px] text-gray-400">Map view with population density</p>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-gray-300 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
          </div>

          {/* FPO Identity */}
          <div className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400 block mb-3">FPO Identity</span>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between"><span className="text-gray-400 font-medium">FPO ID</span><span className="font-bold text-gray-700">FPO-PURI-001</span></div>
              <div className="flex justify-between"><span className="text-gray-400 font-medium">Region</span><span className="text-gray-700">Puri District, Odisha</span></div>
              <div className="flex justify-between"><span className="text-gray-400 font-medium">Established</span><span className="text-gray-700">2021</span></div>
              <div className="flex justify-between items-center"><span className="text-gray-400 font-medium">Status</span><VerificationStamp label="ACTIVE" type="success" compact /></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}