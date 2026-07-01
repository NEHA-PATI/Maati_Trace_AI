import React from "react";
import { Link } from "react-router-dom";
import { MapPin, Hexagon, Calendar, Leaf, Droplets } from "lucide-react";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";

export default function FarmCard({ farm }) {
  const {
    id = "MF-0042",
    surveyNumber = "RS-1204/56",
    village = "Baliguali",
    block = "Puri Sadar",
    district = "Puri",
    area = 2.4,
    crop = "Paddy (Kharif)",
    lastSatelliteDate = "2025-01-15",
    ndvi = 0.62,
    moisture = 0.44,
    status = "verified",
    h3Count = 18,
  } = farm || {};

  const healthColor = ndvi > 0.5 ? "text-primary" : ndvi > 0.3 ? "text-amber-600" : "text-destructive";

  return (
    <Link to={`/land-intelligence/${id}`} className="block group">
      <div className="border border-gray-100 rounded-2xl bg-white hover:shadow-md hover:border-emerald-100 transition-all overflow-hidden shadow-sm">
        {/* Map thumbnail */}
        <div className="h-28 bg-gradient-to-br from-emerald-50 to-green-100 relative overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center opacity-40">
            <div className="w-16 h-12 border-2 border-emerald-400 rounded bg-emerald-200/50" style={{ clipPath: "polygon(20% 0%, 80% 10%, 100% 60%, 70% 100%, 10% 80%)" }} />
          </div>
          <div className="absolute top-2 left-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-white/90 backdrop-blur-sm rounded-full text-[9px] font-semibold text-gray-600 shadow-sm">
              <Hexagon className="w-2.5 h-2.5 text-violet-500" />{h3Count} cells
            </span>
          </div>
          <div className="absolute top-2 right-2">
            <VerificationStamp label={status === "verified" ? "VERIFIED" : "PENDING"} type={status === "verified" ? "success" : "pending"} compact />
          </div>
        </div>

        {/* Data */}
        <div className="p-4 space-y-2.5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-gray-800">{id}</p>
              <p className="text-[10px] text-gray-400">Survey No. {surveyNumber}</p>
            </div>
            <span className="text-sm font-bold text-gray-800">{area} <span className="text-[9px] font-normal text-gray-400">ha</span></span>
          </div>

          <div className="flex items-center gap-1 text-[10px] text-gray-400">
            <MapPin className="w-3 h-3 text-rose-400" />{village}, {block}, {district}
          </div>

          <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1">
              <Leaf className="w-3 h-3 text-emerald-500" />
              <span className={`text-xs font-bold ${healthColor}`}>{ndvi.toFixed(2)}</span>
              <span className="text-[9px] text-gray-400">NDVI</span>
            </div>
            <div className="flex items-center gap-1">
              <Droplets className="w-3 h-3 text-blue-400" />
              <span className="text-xs font-bold text-blue-500">{moisture.toFixed(2)}</span>
              <span className="text-[9px] text-gray-400">MOIST</span>
            </div>
            <div className="flex items-center gap-1 ml-auto">
              <Calendar className="w-3 h-3 text-amber-400" />
              <span className="text-[9px] text-gray-400">{lastSatelliteDate}</span>
            </div>
          </div>

          {crop && (
            <div className="text-[9px] font-semibold uppercase tracking-wider text-gray-400 border-t border-gray-100 pt-1.5">
              🌾 {crop}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}