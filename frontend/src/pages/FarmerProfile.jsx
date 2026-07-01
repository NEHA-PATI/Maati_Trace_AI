import React, { useState, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import {
  User, MapPin, Phone, Mail, Hexagon, Plus, Calendar,
  Leaf, Droplets, Building2, Camera, X, Upload, CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import FarmCard from "@/components/ui-custom/FarmCard";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import FarmerLandMap from "@/components/ui-custom/FarmerLandMap";
import { motion, AnimatePresence } from "framer-motion";

const DEMO_FARMER = {
  id: "FR-001",
  name: "Ramesh Sahoo",
  village: "Baliguali",
  block: "Puri Sadar",
  district: "Puri",
  state: "Odisha",
  phone: "+91 98765 43210",
  email: "ramesh.sahoo@mail.com",
  fpoName: "Puri District FPO",
  fpoId: "FPO-PURI-001",
  aadhaarLast4: "4589",
  registeredDate: "2024-03-15",
  photo: null,
};

// Farms with lat/lng centers so the real Leaflet map can render polygons
const DEMO_FARMS = [
  {
    id: "MF-0042", surveyNumber: "RS-1204/56", village: "Baliguali",
    block: "Puri Sadar", district: "Puri", area: 2.4, crop: "Paddy (Kharif)",
    lastSatelliteDate: "2025-01-15", ndvi: 0.62, moisture: 0.44, status: "verified", h3Count: 18,
    center: [19.812, 85.851],
  },
  {
    id: "MF-0043", surveyNumber: "RS-1205/12", village: "Baliguali",
    block: "Puri Sadar", district: "Puri", area: 3.1, crop: "Groundnut (Rabi)",
    lastSatelliteDate: "2025-01-12", ndvi: 0.48, moisture: 0.38, status: "verified", h3Count: 24,
    center: [19.818, 85.843],
  },
  {
    id: "MF-0044", surveyNumber: "RS-1210/03", village: "Chandanpur",
    block: "Puri Sadar", district: "Puri", area: 1.7, crop: "Sugarcane",
    lastSatelliteDate: "2025-01-10", ndvi: 0.71, moisture: 0.52, status: "pending", h3Count: 12,
    center: [19.805, 85.861],
  },
];

// ── Photo Upload Modal ───────────────────────────────────────────────────────
function PhotoModal({ onClose, onSave }) {
  const fileRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 20 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="relative bg-white rounded-3xl shadow-2xl p-7 w-full max-w-sm z-10"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute top-4 right-4 p-1.5 rounded-xl hover:bg-gray-100 text-gray-400 transition-colors">
          <X className="w-4 h-4" strokeWidth={2.5} />
        </button>

        <div className="text-center mb-5">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center mx-auto mb-3">
            <Camera className="w-6 h-6 text-emerald-500" strokeWidth={2.5} />
          </div>
          <h3 className="font-bold text-gray-800 text-base">Upload Profile Photo</h3>
          <p className="text-xs text-gray-400 mt-1">JPG, PNG or WEBP · Max 5 MB</p>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className={`relative rounded-2xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center py-8 gap-3 ${
            dragging ? "border-emerald-400 bg-emerald-50" : "border-gray-200 hover:border-emerald-300 hover:bg-gray-50"
          }`}
        >
          {preview ? (
            <img src={preview} alt="Preview" className="w-24 h-24 rounded-full object-cover border-4 border-emerald-100 shadow" />
          ) : (
            <>
              <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
                <Upload className="w-5 h-5 text-gray-400" strokeWidth={2.5} />
              </div>
              <span className="text-xs text-gray-400 text-center">Drag & drop or <span className="text-emerald-500 font-semibold">browse</span></span>
            </>
          )}
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
        </div>

        <div className="flex gap-3 mt-5">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-2xl border border-gray-200 text-xs font-medium text-gray-500 hover:bg-gray-50 transition-colors">
            Cancel
          </button>
          <button
            onClick={() => preview && onSave(preview)}
            disabled={!preview}
            className="flex-1 py-2.5 rounded-2xl bg-emerald-500 text-white text-xs font-semibold hover:bg-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5" strokeWidth={2.5} />Save Photo
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function FarmerProfile() {
  const { farmerId } = useParams();
  const [farmer, setFarmer] = useState(DEMO_FARMER);
  const [showPhotoModal, setShowPhotoModal] = useState(false);
  const farms = DEMO_FARMS;
  const totalArea = farms.reduce((s, f) => s + f.area, 0);
  const avgNdvi = farms.reduce((s, f) => s + f.ndvi, 0) / farms.length;

  const handleSavePhoto = (dataUrl) => {
    setFarmer(prev => ({ ...prev, photo: dataUrl }));
    setShowPhotoModal(false);
  };

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto" style={{ fontFamily: "'Poppins', sans-serif" }}>
      {/* Photo modal */}
      <AnimatePresence>
        {showPhotoModal && (
          <PhotoModal onClose={() => setShowPhotoModal(false)} onSave={handleSavePhoto} />
        )}
      </AnimatePresence>

      {/* ── Identity Card ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm"
      >
        <div className="px-5 py-3 bg-gray-50/80 border-b border-gray-100 flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">Field Record — Farmer Identity</span>
          <VerificationStamp label="REGISTERED" type="success" compact />
        </div>

        <div className="p-5 md:p-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* ── Circular photo ── */}
            <div className="flex-shrink-0 flex flex-col items-center gap-2">
              <div className="relative">
                <div className="w-24 h-24 rounded-full border-4 border-emerald-100 shadow-md overflow-hidden bg-gray-50 flex items-center justify-center">
                  {farmer.photo ? (
                    <img src={farmer.photo} alt={farmer.name} className="w-full h-full object-cover" />
                  ) : (
                    <User className="w-10 h-10 text-gray-300" strokeWidth={1.5} />
                  )}
                </div>
                {/* + / Camera button */}
                <button
                  onClick={() => setShowPhotoModal(true)}
                  className="absolute bottom-0 right-0 w-7 h-7 rounded-full bg-emerald-500 hover:bg-emerald-600 border-2 border-white flex items-center justify-center shadow transition-colors"
                  title="Upload photo"
                >
                  {farmer.photo ? (
                    <Camera className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
                  ) : (
                    <Plus className="w-3.5 h-3.5 text-white" strokeWidth={3} />
                  )}
                </button>
              </div>
              <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">ID: {farmer.id}</span>
            </div>

            {/* Identity details */}
            <div className="flex-1 space-y-4">
              <div>
                <h1 className="text-xl font-bold text-gray-800">{farmer.name}</h1>
                <div className="flex flex-wrap items-center gap-3 mt-1.5">
                  <span className="flex items-center gap-1.5 text-xs text-gray-500">
                    <MapPin className="w-3.5 h-3.5 text-rose-400" strokeWidth={2.5} />
                    {farmer.village}, {farmer.block}, {farmer.district}
                  </span>
                  <span className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Building2 className="w-3.5 h-3.5 text-blue-400" strokeWidth={2.5} />
                    {farmer.fpoName}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-400 block">Phone</span>
                  <span className="text-xs font-semibold text-gray-700 flex items-center gap-1">
                    <Phone className="w-3 h-3 text-emerald-400" strokeWidth={2.5} />{farmer.phone}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-400 block">Email</span>
                  <span className="text-xs font-semibold text-gray-700 flex items-center gap-1 truncate">
                    <Mail className="w-3 h-3 text-blue-400 flex-shrink-0" strokeWidth={2.5} />{farmer.email}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-400 block">Aadhaar</span>
                  <span className="text-xs font-semibold text-gray-700">XXXX-XXXX-{farmer.aadhaarLast4}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-400 block">Registered</span>
                  <span className="text-xs font-semibold text-gray-700 flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-amber-400" strokeWidth={2.5} />{farmer.registeredDate}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Stat Strip ── */}
      <StatStrip items={[
        { label: "Total Farms", value: farms.length, icon: MapPin },
        { label: "Total Area", value: totalArea.toFixed(1), unit: "ha", icon: Hexagon },
        { label: "Avg. Vegetation", value: avgNdvi.toFixed(2), unit: "NDVI", icon: Leaf },
        { label: "Latest Scene", value: "Jan 15", sub: "2025", icon: Calendar },
      ]} />

      {/* ── Real Leaflet Map with all farm polygons ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden"
      >
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm font-bold text-gray-800">Farm Land Map</span>
          <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">
            {farms.length} parcels · Click marker to open
          </span>
        </div>
        <div className="p-0">
          <FarmerLandMap farms={farms} />
        </div>
      </motion.div>

      {/* ── Farm Cards + Sidebar ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-gray-800">Registered Land Parcels</h2>
            <Link to="/farm-register">
              <Button size="sm" variant="outline" className="h-7 text-[10px] font-semibold uppercase tracking-wider rounded-2xl">
                <Plus className="w-3 h-3 mr-1" strokeWidth={2.5} />Register Farm
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {farms.map((farm, i) => (
              <motion.div
                key={farm.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <FarmCard farm={farm} />
              </motion.div>
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Average Health */}
          <div className="bg-white border border-gray-100 rounded-3xl p-5 shadow-sm">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block mb-4">Average Farm Health</span>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-gray-600 font-medium">
                    <Leaf className="w-3.5 h-3.5 text-emerald-500" strokeWidth={2.5} />Vegetation Index
                  </span>
                  <span className="font-bold text-emerald-600">{avgNdvi.toFixed(2)}</span>
                </div>
                <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${avgNdvi * 100}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-gray-600 font-medium">
                    <Droplets className="w-3.5 h-3.5 text-blue-500" strokeWidth={2.5} />Moisture Index
                  </span>
                  <span className="font-bold text-blue-600">0.45</span>
                </div>
                <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "45%" }}
                    transition={{ duration: 1, delay: 0.5 }}
                    className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Notifications */}
          <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <span className="text-sm font-bold text-gray-800">Alerts</span>
              <span className="w-2 h-2 bg-rose-400 rounded-full pulse-live" />
            </div>
            <div className="p-2">
              <NotificationStack limit={3} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}