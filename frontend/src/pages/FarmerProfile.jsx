import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  User, MapPin, Phone, Mail, Hexagon, Plus, Calendar,
  Leaf, Droplets, Building2, Camera, X, Upload, CheckCircle2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import FarmCard from "@/components/ui-custom/FarmCard";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import FarmerLandMap from "@/components/ui-custom/FarmerLandMap";
import FarmPointerMap from "@/components/ui-custom/FarmPointerMap";
import {
  getFarmer,
  getFarmerFarms,
  getFarmerSummary,
  getMyFarmerProfile,
} from "@/lib/api/farmer";
import { getStoredUser } from "@/lib/auth/session";

const DEFAULT_FARMER = {
  id: "FR-000",
  name: "Farmer profile",
  village: "Not available",
  block: "Not available",
  district: "Not available",
  state: "Odisha",
  phone: "Not available",
  email: "Not available",
  fpoName: "Independent farmer",
  fpoId: null,
  aadhaarLast4: "----",
  registeredDate: "Active profile",
  photo: null,
};

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
        className="relative z-10 w-full max-w-sm rounded-3xl bg-white p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute right-4 top-4 rounded-xl p-1.5 text-gray-400 transition-colors hover:bg-gray-100">
          <X className="h-4 w-4" strokeWidth={2.5} />
        </button>

        <div className="mb-5 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50">
            <Camera className="h-6 w-6 text-emerald-500" strokeWidth={2.5} />
          </div>
          <h3 className="text-base font-bold text-gray-800">Upload Profile Photo</h3>
          <p className="mt-1 text-xs text-gray-400">JPG, PNG or WEBP · Max 5 MB</p>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className={`relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed py-8 transition-all ${
            dragging ? "border-emerald-400 bg-emerald-50" : "border-gray-200 hover:border-emerald-300 hover:bg-gray-50"
          }`}
        >
          {preview ? (
            <img src={preview} alt="Preview" className="h-24 w-24 rounded-full border-4 border-emerald-100 object-cover shadow" />
          ) : (
            <>
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100">
                <Upload className="h-5 w-5 text-gray-400" strokeWidth={2.5} />
              </div>
              <span className="text-center text-xs text-gray-400">
                Drag and drop or <span className="font-semibold text-emerald-500">browse</span>
              </span>
            </>
          )}
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
        </div>

        <div className="mt-5 flex gap-3">
          <button onClick={onClose} className="flex-1 rounded-2xl border border-gray-200 py-2.5 text-xs font-medium text-gray-500 transition-colors hover:bg-gray-50">
            Cancel
          </button>
          <button
            onClick={() => preview && onSave(preview)}
            disabled={!preview}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-2xl bg-emerald-500 py-2.5 text-xs font-semibold text-white transition-colors hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <CheckCircle2 className="h-3.5 w-3.5" strokeWidth={2.5} />
            Save Photo
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default function FarmerProfile() {
  const { farmerId } = useParams();
  const location = useLocation();
  const user = getStoredUser();
  const isSelfRoute = location.pathname === "/farmer/me";

  const [farmer, setFarmer] = useState(DEFAULT_FARMER);
  const [farms, setFarms] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showPhotoModal, setShowPhotoModal] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      setLoading(true);
      setError("");

      try {
        const farmerPayload = isSelfRoute
          ? await getMyFarmerProfile()
          : await getFarmer(farmerId);

        const [summaryPayload, farmsPayload] = await Promise.all([
          getFarmerSummary(farmerPayload.farmer_id).catch(() => null),
          getFarmerFarms(farmerPayload.farmer_id).catch(() => []),
        ]);

        if (cancelled) return;

        setSummary(summaryPayload);
        setFarmer((prev) => ({
          ...prev,
          id: farmerPayload.farmer_id,
          name: farmerPayload.full_name || "Unnamed farmer",
          village: farmerPayload.village_name || "Village unavailable",
          block: farmerPayload.block_name || "Block unavailable",
          district: farmerPayload.district_name || "District unavailable",
          state: farmerPayload.state_name || "Odisha",
          phone: farmerPayload.phone_number || user?.phone_number || "Not available",
          email: user?.email || "Not available",
          fpoName: summaryPayload?.fpo_name || "Independent farmer",
          fpoId: farmerPayload.fpo_id || null,
        }));

        setFarms(
          (farmsPayload || []).map((farmItem) => {
            const polygon = farmItem.polygon_geojson?.coordinates?.[0] || [];
            const center =
              farmItem.bbox?.length === 4
                ? [
                    (farmItem.bbox[1] + farmItem.bbox[3]) / 2,
                    (farmItem.bbox[0] + farmItem.bbox[2]) / 2,
                  ]
                : polygon[0]
                  ? [polygon[0][1], polygon[0][0]]
                  : [20.2961, 85.8245];

            return {
              id: farmItem.farm_id,
              surveyNumber: farmItem.survey_number || "Survey pending",
              village: farmItem.village_name || farmerPayload.village_name || "Village unavailable",
              block: farmItem.block_name || farmerPayload.block_name || "Block unavailable",
              district: farmItem.district_name || farmerPayload.district_name || "District unavailable",
              area: Number(farmItem.area_acres || 0),
              crop: "Crop data pending",
              lastSatelliteDate: summaryPayload?.latest_observation_date || "Pending",
              ndvi: Number(summaryPayload?.avg_ndvi || 0),
              moisture: Number(summaryPayload?.avg_ndmi || 0),
              status: farmItem.is_active ? "verified" : "pending",
              h3Count: farmItem.h3_cell_count || 0,
              center,
              polygon: polygon.map(([lng, lat]) => [lat, lng]),
              farmName: farmItem.farm_name || "Registered farm",
            };
          }),
        );
      } catch (err) {
        if (cancelled) return;
        setError(typeof err?.message === "string" ? err.message : "Unable to load farmer profile.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, [farmerId, isSelfRoute, user?.email, user?.phone_number]);

  const totalArea = useMemo(
    () => farms.reduce((sum, item) => sum + Number(item.area || 0), 0),
    [farms],
  );

  const avgNdvi = useMemo(() => {
    if (!farms.length) return Number(summary?.avg_ndvi || 0);
    const total = farms.reduce((sum, item) => sum + Number(item.ndvi || 0), 0);
    return total / farms.length;
  }, [farms, summary]);

  const avgMoisture = useMemo(() => {
    if (!farms.length) return Number(summary?.avg_ndmi || 0);
    const total = farms.reduce((sum, item) => sum + Number(item.moisture || 0), 0);
    return total / farms.length;
  }, [farms, summary]);

  const handleSavePhoto = (dataUrl) => {
    setFarmer((prev) => ({ ...prev, photo: dataUrl }));
    setShowPhotoModal(false);
  };

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <AnimatePresence>
        {showPhotoModal && (
          <PhotoModal onClose={() => setShowPhotoModal(false)} onSave={handleSavePhoto} />
        )}
      </AnimatePresence>

      {loading && (
        <div className="rounded-3xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">
          Loading farmer profile...
        </div>
      )}

      {!loading && error && (
        <div className="rounded-3xl border border-rose-100 bg-rose-50 p-6 text-sm text-rose-600 shadow-sm">
          {error}
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm"
      >
        <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/80 px-5 py-3">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">Field Record - Farmer Identity</span>
          <VerificationStamp label="REGISTERED" type="success" compact />
        </div>

        <div className="p-5 md:p-6">
          <div className="flex flex-col gap-6 md:flex-row">
            <div className="flex flex-shrink-0 flex-col items-center gap-2">
              <div className="relative">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-4 border-emerald-100 bg-gray-50 shadow-md">
                  {farmer.photo ? (
                    <img src={farmer.photo} alt={farmer.name} className="h-full w-full object-cover" />
                  ) : (
                    <User className="h-10 w-10 text-gray-300" strokeWidth={1.5} />
                  )}
                </div>
                <button
                  onClick={() => setShowPhotoModal(true)}
                  className="absolute bottom-0 right-0 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white bg-emerald-500 shadow transition-colors hover:bg-emerald-600"
                  title="Upload photo"
                >
                  {farmer.photo ? (
                    <Camera className="h-3.5 w-3.5 text-white" strokeWidth={2.5} />
                  ) : (
                    <Plus className="h-3.5 w-3.5 text-white" strokeWidth={3} />
                  )}
                </button>
              </div>
              <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">ID: {farmer.id}</span>
            </div>

            <div className="flex-1 space-y-4">
              <div>
                <h1 className="text-xl font-bold text-gray-800">{farmer.name}</h1>
                <div className="mt-1.5 flex flex-wrap items-center gap-3">
                  <span className="flex items-center gap-1.5 text-xs text-gray-500">
                    <MapPin className="h-3.5 w-3.5 text-rose-400" strokeWidth={2.5} />
                    {farmer.village}, {farmer.block}, {farmer.district}
                  </span>
                  <span className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Building2 className="h-3.5 w-3.5 text-blue-400" strokeWidth={2.5} />
                    {farmer.fpoName}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <div className="space-y-1">
                  <span className="block text-[9px] font-semibold uppercase tracking-widest text-gray-400">Phone</span>
                  <span className="flex items-center gap-1 text-xs font-semibold text-gray-700">
                    <Phone className="h-3 w-3 text-emerald-400" strokeWidth={2.5} />
                    {farmer.phone}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="block text-[9px] font-semibold uppercase tracking-widest text-gray-400">Email</span>
                  <span className="flex items-center gap-1 truncate text-xs font-semibold text-gray-700">
                    <Mail className="h-3 w-3 flex-shrink-0 text-blue-400" strokeWidth={2.5} />
                    {farmer.email}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="block text-[9px] font-semibold uppercase tracking-widest text-gray-400">Aadhaar</span>
                  <span className="text-xs font-semibold text-gray-700">XXXX-XXXX-{farmer.aadhaarLast4}</span>
                </div>
                <div className="space-y-1">
                  <span className="block text-[9px] font-semibold uppercase tracking-widest text-gray-400">Registered</span>
                  <span className="flex items-center gap-1 text-xs font-semibold text-gray-700">
                    <Calendar className="h-3 w-3 text-amber-400" strokeWidth={2.5} />
                    {farmer.registeredDate}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <StatStrip items={[
        { label: "Total Farms", value: farms.length, icon: MapPin },
        { label: "Total Area", value: totalArea.toFixed(1), unit: "ac", icon: Hexagon },
        { label: "Avg. Vegetation", value: avgNdvi.toFixed(2), unit: "NDVI", icon: Leaf },
        { label: "Latest Scene", value: summary?.latest_observation_date || "Pending", icon: Calendar },
      ]} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm"
      >
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3">
          <span className="text-sm font-bold text-gray-800">Farm Land Map</span>
          <span className="text-[10px] font-medium uppercase tracking-wider text-gray-400">
            {farms.length} parcels - Click marker to open
          </span>
        </div>
        <FarmerLandMap farms={farms} />
      </motion.div>

      <div className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3">
          <span className="text-sm font-bold text-gray-800">Farm Pointers</span>
          <span className="text-[10px] font-medium uppercase tracking-wider text-gray-400">{farms.length} farms</span>
        </div>
        <div className="p-3">
          <FarmPointerMap
            farms={farms.map((farmItem) => ({
              farm_id: farmItem.id,
              farm_name: farmItem.farmName || farmItem.surveyNumber || "Registered farm",
              farmer_id: farmer.id,
              fpo_id: farmer.fpoId,
              village_name: farmItem.village,
              district_name: farmItem.district,
              block_name: farmItem.block,
              area_acres: farmItem.area,
              bbox: farmItem.bbox,
              polygon_geojson: farmItem.polygon?.length
                ? {
                    type: "Polygon",
                    coordinates: [
                      [...farmItem.polygon.map(([lat, lon]) => [lon, lat]), [farmItem.polygon[0][1], farmItem.polygon[0][0]]],
                    ],
                  }
                : null,
              h3_cell_count: farmItem.h3Count,
              latest_ndvi: farmItem.ndvi,
              latest_ndmi: farmItem.moisture,
              health_status: farmItem.status === "verified" ? "stable" : "unknown",
            }))}
            onFarmClick={(farmItem) => window.location.assign(`/land/${farmItem.farm_id}`)}
            showBoundaries
            height={420}
            userRole={user?.role}
            emptyMessage="No farms linked to this farmer yet."
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-gray-800">Registered Land Parcels</h2>
            <Link to="/farm-register">
              <Button size="sm" variant="outline" className="h-7 rounded-2xl text-[10px] font-semibold uppercase tracking-wider">
                <Plus className="mr-1 h-3 w-3" strokeWidth={2.5} />
                Register Farm
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {farms.map((farmItem, index) => (
              <motion.div
                key={farmItem.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <FarmCard farm={farmItem} />
              </motion.div>
            ))}
          </div>
          {!loading && !error && farms.length === 0 && (
            <div className="rounded-3xl border border-dashed border-gray-200 bg-white p-6 text-sm text-gray-500 shadow-sm">
              No farms are linked to this farmer yet.
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="rounded-3xl border border-gray-100 bg-white p-5 shadow-sm">
            <span className="mb-4 block text-xs font-bold uppercase tracking-widest text-gray-500">Average Farm Health</span>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-gray-600">
                    <Leaf className="h-3.5 w-3.5 text-emerald-500" strokeWidth={2.5} />
                    Vegetation Index
                  </span>
                  <span className="font-bold text-emerald-600">{avgNdvi.toFixed(2)}</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-gray-100">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.max(0, Math.min(100, avgNdvi * 100))}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-gray-600">
                    <Droplets className="h-3.5 w-3.5 text-blue-500" strokeWidth={2.5} />
                    Moisture Index
                  </span>
                  <span className="font-bold text-blue-600">{avgMoisture.toFixed(2)}</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-gray-100">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.max(0, Math.min(100, avgMoisture * 100))}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                    className="h-full rounded-full bg-gradient-to-r from-blue-400 to-blue-600"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="text-sm font-bold text-gray-800">Alerts</span>
              <span className="pulse-live h-2 w-2 rounded-full bg-rose-400" />
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
