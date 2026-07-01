import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell, AlertTriangle, Info, CheckCircle, ChevronRight,
  Leaf, Droplets, Satellite, MapPin, User
} from "lucide-react";
import { motion } from "framer-motion";

// Farm map snapshot thumbnail (real satellite/field imagery)
const FARM_THUMBNAILS = {
  "MF-0042": "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg",
  "MF-0043": "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/34_sgalr8.jpg",
  "MF-0089": "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg",
};

// FPO vs individual farmer type
// type: "fpo" shows farm thumbnail + farmer icon; type: "farmer" shows only farm thumbnail
const ALL_NOTIFICATIONS = [
  {
    id: 1,
    priority: "high",
    icon: Droplets,
    title: "Moisture Stress Detected",
    detail: "Farm MF-0042 — Puri Sadar Block. NDMI dropped below 0.2 in 4 H3 cells.",
    time: "12 min ago",
    farmId: "MF-0042",
    notifType: "fpo",
    farmerName: "Ramesh Sahoo",
    farmerVillage: "Tangi Village",
  },
  {
    id: 2,
    priority: "high",
    icon: AlertTriangle,
    title: "Cloud Cover Warning",
    detail: "Latest Sentinel-2 scene for Nayagarh district — 78% cloud cover. Scene marked unusable.",
    time: "1 hr ago",
    farmId: null,
    notifType: "system",
  },
  {
    id: 3,
    priority: "high",
    icon: Leaf,
    title: "Vegetation Anomaly",
    detail: "Farm MF-0043 — NDVI deviation detected in cells 08–12. Decline of 0.15 from 14-day average.",
    time: "2 hrs ago",
    farmId: "MF-0043",
    notifType: "farmer",
  },
  {
    id: 4,
    priority: "medium",
    icon: MapPin,
    title: "New Farm Registered",
    detail: "Farm MF-0089 in Khurda Block — location verified, 14 H3 cells generated.",
    time: "3 hrs ago",
    farmId: "MF-0089",
    notifType: "fpo",
    farmerName: "Suresh Nayak",
    farmerVillage: "Bhubaneswar Block",
  },
  {
    id: 5,
    priority: "medium",
    icon: Satellite,
    title: "Raster Processing Complete",
    detail: "Batch B-0034 — 34 farms processed. 32 successful, 2 failed cloud validation.",
    time: "5 hrs ago",
    farmId: null,
    notifType: "system",
  },
  {
    id: 6,
    priority: "medium",
    icon: CheckCircle,
    title: "Bulk Upload Processed",
    detail: "CSV batch from FPO-PURI-001 — 6 rows. 4 registered successfully, 2 validation errors.",
    time: "6 hrs ago",
    farmId: null,
    notifType: "system",
  },
  {
    id: 7,
    priority: "low",
    icon: Satellite,
    title: "Satellite Scene Available",
    detail: "Sentinel-2B scene dated 2025-01-15 indexed for Puri district. Cloud cover: 12.4%.",
    time: "8 hrs ago",
    farmId: null,
    notifType: "system",
  },
  {
    id: 8,
    priority: "low",
    icon: Leaf,
    title: "Vegetation Growth Trend",
    detail: "Farm MF-0042 — NDVI trend +0.08 over 30 days. Growth trajectory normal for kharif season.",
    time: "12 hrs ago",
    farmId: "MF-0042",
    notifType: "farmer",
  },
];

const PRIORITY_CONFIG = {
  high:   { dot: "bg-red-400",    ring: "ring-red-100",    badge: "bg-red-50 text-red-600",    bar: "bg-red-300",   label: "Critical" },
  medium: { dot: "bg-amber-400",  ring: "ring-amber-100",  badge: "bg-amber-50 text-amber-700", bar: "bg-amber-300", label: "Warning" },
  low:    { dot: "bg-emerald-400",ring: "ring-emerald-100",badge: "bg-emerald-50 text-emerald-700", bar: "bg-emerald-300", label: "Info" },
};

export default function Notifications() {
  const [filter, setFilter] = useState("all");

  const filtered = filter === "all"
    ? ALL_NOTIFICATIONS
    : ALL_NOTIFICATIONS.filter(n => n.priority === filter);

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-5" style={{ fontFamily: "'Poppins', sans-serif" }}>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900 tracking-tight">Notifications</h1>
          <p className="text-xs text-gray-400 mt-0.5">Alerts, predictions and system updates</p>
        </div>
        <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1">
          {["all", "high", "medium", "low"].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-lg text-[11px] font-medium capitalize transition-all ${
                filter === f
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-400 hover:text-gray-700"
              }`}
            >
              {f}
              {f === "high" && (
                <span className="ml-1 w-1.5 h-1.5 bg-red-400 rounded-full inline-block align-middle" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Notification cards */}
      <div className="space-y-3">
        {filtered.map((n, i) => {
          const Icon = n.icon;
          const cfg = PRIORITY_CONFIG[n.priority];
          const thumb = n.farmId ? FARM_THUMBNAILS[n.farmId] : null;
          const showFarmerIcon = n.notifType === "fpo";

          return (
            <motion.div
              key={n.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
            >
              {/* Priority accent bar top */}
              <div className={`h-0.5 w-full ${cfg.bar} opacity-60`} />

              <div className="p-4 flex gap-3">
                {/* Icon bubble */}
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ring-4 ${cfg.badge} ${cfg.ring}`}>
                  <Icon className="w-4 h-4" />
                </div>

                {/* Main content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-gray-900 leading-snug">{n.title}</h3>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {n.priority === "high" && (
                        <span className="w-1.5 h-1.5 rounded-full bg-red-400 pulse-live flex-shrink-0" />
                      )}
                      <span className={`text-[9px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${cfg.badge}`}>
                        {cfg.label}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 leading-relaxed mb-2">{n.detail}</p>

                  {/* Thumbnails row — farm map + farmer icon */}
                  {(thumb || showFarmerIcon) && (
                    <div className="flex items-center gap-2 mb-2">
                      {/* Farm map snapshot — always shown if farmId exists */}
                      {thumb && (
                        <div className="w-14 h-10 rounded-lg overflow-hidden border border-gray-200 flex-shrink-0">
                          <img src={thumb} alt="Farm map" className="w-full h-full object-cover" />
                        </div>
                      )}
                      {/* Farmer identity chip — only for FPO notifications */}
                      {showFarmerIcon && n.farmerName && (
                        <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-100 rounded-lg px-2 py-1">
                          <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
                            <User className="w-3 h-3 text-emerald-600" />
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold text-gray-700 leading-none">{n.farmerName}</p>
                            <p className="text-[9px] text-gray-400 leading-none mt-0.5">{n.farmerVillage}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Footer row */}
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-gray-300">{n.time}</span>
                    {n.farmId && (
                      <Link
                        to={`/land-intelligence/${n.farmId}`}
                        className="text-[10px] font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-0.5 ml-auto"
                      >
                        View Farm <ChevronRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}