import React from "react";
import { Link } from "react-router-dom";
import { 
  Server, Users, MapPin, Hexagon, BarChart3, AlertTriangle,
  CheckCircle, XCircle, Activity, Database, Satellite, Layers,
  ChevronRight, RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import { motion } from "framer-motion";

const SERVICES = [
  { name: "District Boundary Service", port: 8005, status: "healthy", uptime: "99.8%", icon: MapPin },
  { name: "Farm Registry Service", port: 8006, status: "healthy", uptime: "99.9%", icon: Database },
  { name: "Boundary Index Service", port: 8004, status: "healthy", uptime: "99.7%", icon: Hexagon },
  { name: "STAC Catalog Service", port: 8007, status: "healthy", uptime: "99.5%", icon: Satellite },
  { name: "Raster Processor Service", port: 8008, status: "degraded", uptime: "97.2%", icon: Layers },
];

const DISTRICTS = [
  { name: "Puri", fpos: 3, farmers: 447, farms: 978, hectares: 2647, coverage: 72 },
  { name: "Khurda", fpos: 2, farmers: 312, farms: 689, hectares: 1834, coverage: 58 },
  { name: "Nayagarh", fpos: 2, farmers: 234, farms: 512, hectares: 1389, coverage: 45 },
  { name: "Cuttack", fpos: 4, farmers: 567, farms: 1234, hectares: 3456, coverage: 65 },
  { name: "Ganjam", fpos: 3, farmers: 389, farms: 845, hectares: 2234, coverage: 52 },
];

export default function AdminDashboard() {
  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Admin Command Center</h1>
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-0.5">Platform-wide overview — MaatiTrace Operations</p>
        </div>
        <Button size="sm" variant="outline" className="h-9 text-xs font-semibold rounded-xl border-gray-200 hover:bg-gray-50">
          <RefreshCw className="w-3 h-3 mr-1 text-blue-500" />Refresh
        </Button>
      </div>

      <StatStrip items={[
        { label: "Total FPOs", value: "14", icon: Users },
        { label: "Registered Farmers", value: "1,949", icon: Users },
        { label: "Total Farms", value: "4,258", icon: MapPin },
        { label: "Total Hectares", value: "11,560", unit: "ha", icon: Layers },
        { label: "Failed Jobs", value: "7", icon: AlertTriangle, sub: "Last 24h" },
      ]} />

      {/* Service Health */}
      <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-500" />Service Health
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">All Systems Monitored</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 divide-x divide-gray-50">
          {SERVICES.map((svc, i) => {
            const Icon = svc.icon;
            const isHealthy = svc.status === "healthy";
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${isHealthy ? "bg-emerald-50" : "bg-amber-50"}`}>
                    <Icon className={`w-3.5 h-3.5 ${isHealthy ? "text-emerald-500" : "text-amber-500"}`} />
                  </div>
                  <div className={`w-1.5 h-1.5 rounded-full ${isHealthy ? "bg-emerald-400" : "bg-amber-400"} ${!isHealthy ? "pulse-live" : ""}`} />
                </div>
                <p className="text-[10px] font-semibold text-gray-700 leading-tight mb-1">{svc.name}</p>
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-gray-400 font-mono">:{svc.port}</span>
                  <VerificationStamp label={svc.status.toUpperCase()} type={isHealthy ? "success" : "warning"} compact />
                </div>
                <p className="text-[9px] text-gray-400 mt-1">Uptime: {svc.uptime}</p>
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* District Coverage */}
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-blue-500" />District Coverage — Odisha
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    {["District", "FPOs", "Farmers", "Farms", "Hectares", "Coverage"].map(h => (
                      <th key={h} className="text-left px-4 py-2.5 font-semibold uppercase tracking-wider text-[9px] text-gray-400">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {DISTRICTS.map(d => (
                    <tr key={d.name} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors">
                      <td className="px-4 py-2.5 font-bold text-gray-700">{d.name}</td>
                      <td className="px-4 py-2.5 text-gray-600">{d.fpos}</td>
                      <td className="px-4 py-2.5 font-bold text-gray-700">{d.farmers}</td>
                      <td className="px-4 py-2.5 text-gray-600">{d.farms}</td>
                      <td className="px-4 py-2.5 text-gray-600">{d.hectares.toLocaleString()}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full" style={{ width: `${d.coverage}%` }} />
                          </div>
                          <span className="font-bold text-emerald-600">{d.coverage}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Processing */}
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <Layers className="w-4 h-4 text-violet-500" />Recent Raster Processing
              </span>
            </div>
            <div className="p-4 space-y-2">
              {[
                { batch: "B-0034", farms: 34, status: "completed", time: "12 min ago", failed: 2 },
                { batch: "B-0033", farms: 28, status: "completed", time: "1 hr ago", failed: 0 },
                { batch: "B-0032", farms: 45, status: "completed", time: "3 hrs ago", failed: 5 },
                { batch: "B-0031", farms: 12, status: "failed", time: "4 hrs ago", failed: 12 },
              ].map(b => (
                <div key={b.batch} className="flex items-center justify-between p-3 border border-gray-100 rounded-xl hover:bg-gray-50/70 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${b.status === "completed" ? "bg-emerald-50" : "bg-rose-50"}`}>
                      {b.status === "completed"
                        ? <CheckCircle className="w-4 h-4 text-emerald-500" />
                        : <XCircle className="w-4 h-4 text-rose-500" />}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-gray-700">{b.batch}</span>
                      <span className="text-[10px] text-gray-400 ml-2">{b.farms} farms</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-gray-400">
                    {b.failed > 0 && <span className="text-rose-500 font-medium">{b.failed} failed</span>}
                    <span>{b.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div className="space-y-5">
          <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />System Alerts
              </span>
              <span className="w-2 h-2 bg-rose-400 rounded-full pulse-live" />
            </div>
            <div className="p-2">
              <NotificationStack limit={5} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}