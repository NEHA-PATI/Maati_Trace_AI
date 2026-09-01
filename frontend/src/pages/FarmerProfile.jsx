import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  User, MapPin, Phone, Hexagon, Plus, Calendar,
  Leaf, Droplets, Camera, X, Upload, CheckCircle2,
  BadgeCheck, Pencil, Map as MapIcon, Bell,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import StatStrip from "@/components/ui-custom/StatStrip";
import FarmCard from "@/components/ui-custom/FarmCard";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import FarmerLandMap from "@/components/ui-custom/FarmerLandMap";
import FarmPointerMap from "@/components/ui-custom/FarmPointerMap";
import {
  getFarmer,
  getFarmerFarms,
  getFarmerSummary,
  getMyFarmerProfile,
} from "@/lib/api/farmer";
import { getStoredUser } from "@/features/auth/session";

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
          <p className="mt-1 text-xs text-gray-400">JPG, PNG or WEBP Â· Max 5 MB</p>
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

  const firstName = (farmer.name || "").trim().split(/\s+/)[0] || "there";
  const healthLabel =
    !avgNdvi || avgNdvi <= 0
      ? "Checking"
      : avgNdvi > 0.5
        ? "Healthy"
        : avgNdvi > 0.3
          ? "Okay"
          : "Needs care";
  const lastCheck = summary?.latest_observation_date || "Waiting";

  const callablePhoneHref = useMemo(() => {
    const raw = farmer.phone;
    if (!raw || raw === "Not available") return null;
    const digitsAndPlus = String(raw).replace(/(?!^\+)[^\d]/g, "");
    const normalised = digitsAndPlus.startsWith("+")
      ? digitsAndPlus
      : digitsAndPlus.length === 10
        ? `+91${digitsAndPlus}`
        : digitsAndPlus;
    return normalised ? `tel:${normalised}` : null;
  }, [farmer.phone]);

  return (
    <div className="mt-surface mx-auto max-w-[1180px] space-y-4 p-4 md:p-6">
      <AnimatePresence>
        {showPhotoModal && (
          <PhotoModal onClose={() => setShowPhotoModal(false)} onSave={handleSavePhoto} />
        )}
      </AnimatePresence>

      <div>
        <h1 className="text-[22px] font-extrabold text-[var(--mt-ink)]">Welcome back, {firstName}</h1>
        <p className="mt-0.5 text-[13px] font-semibold text-[var(--mt-ink-soft)]">
          Here&rsquo;s how your farms are doing today
        </p>
      </div>

      {loading && (
        <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-6 text-sm font-semibold text-[var(--mt-ink-soft)]">
          Loading your profile…
        </div>
      )}

      {!loading && error && (
        <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-clay)]/30 bg-[var(--mt-clay-tint)] p-6 text-sm font-semibold text-[var(--mt-clay-text)]">
          {error}
        </div>
      )}

      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col gap-4 rounded-[var(--mt-radius-lg)] border border-[var(--mt-line)] bg-white p-5 md:flex-row md:flex-wrap md:items-center md:justify-between md:gap-5 md:p-6"
      >
        <div className="flex items-center gap-4">
          <div className="relative shrink-0">
            <div className="flex h-[68px] w-[68px] items-center justify-center overflow-hidden rounded-full bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]">
              {farmer.photo ? (
                <img src={farmer.photo} alt={farmer.name} className="h-full w-full object-cover" />
              ) : (
                <User className="h-8 w-8" strokeWidth={2} />
              )}
            </div>
            <button
              onClick={() => setShowPhotoModal(true)}
              className="absolute -bottom-0.5 -right-0.5 flex h-[26px] w-[26px] items-center justify-center rounded-full border-2 border-white bg-[var(--mt-leaf)] text-white"
              aria-label="Change profile photo"
              title="Change profile photo"
            >
              {farmer.photo ? <Camera className="h-3.5 w-3.5" strokeWidth={2.6} /> : <Plus className="h-3.5 w-3.5" strokeWidth={3} />}
            </button>
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[19px] font-extrabold text-[var(--mt-ink)] sm:text-[21px]">{farmer.name}</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-[var(--mt-leaf)] px-2.5 py-1 text-[11.5px] font-bold text-white">
                <BadgeCheck className="h-3.5 w-3.5" strokeWidth={2.6} />
                Registered
              </span>
            </div>
            <div className="mt-1.5 flex items-center gap-1.5 text-[13.5px] font-semibold text-[var(--mt-ink-soft)]">
              <MapPin className="h-3.5 w-3.5 shrink-0 text-[var(--mt-clay)]" strokeWidth={2.2} />
              <span className="truncate">{[farmer.village, farmer.block, farmer.district].filter(Boolean).join(", ")}</span>
            </div>
            <span className="mt-2 inline-block rounded-full bg-[var(--mt-leaf-tint)] px-3 py-1 text-[12px] font-bold text-[var(--mt-leaf-deep)]">
              {farmer.fpoName}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 border-t border-[var(--mt-line)] pt-4 md:flex md:w-auto md:gap-8 md:border-0 md:px-1 md:pt-0">
          <div>
            <div className="text-[11px] font-bold text-[var(--mt-ink-faint)]">Phone</div>
            <div className="mt-1 flex items-center gap-1.5 text-[14px] font-bold text-[var(--mt-ink)]">
              <Phone className="h-3.5 w-3.5 shrink-0 text-[var(--mt-leaf)]" strokeWidth={2.4} />
              <span className="truncate">{farmer.phone}</span>
            </div>
          </div>
          <div>
            <div className="text-[11px] font-bold text-[var(--mt-ink-faint)]">ID Card</div>
            <div className="mt-1 flex items-center gap-1.5 text-[14px] font-bold text-[var(--mt-ink)]">
              <BadgeCheck className="h-3.5 w-3.5 text-[var(--mt-leaf)]" strokeWidth={2.6} />
              Verified
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2.5 md:flex md:w-auto">
          {callablePhoneHref ? (
            <a
              href={callablePhoneHref}
              className="flex h-11 items-center justify-center gap-2 rounded-full bg-[var(--mt-leaf)] px-4 text-[13.5px] font-bold text-white"
            >
              <Phone className="h-4 w-4" strokeWidth={2.4} />
              Call Me
            </a>
          ) : (
            <span className="flex h-11 items-center justify-center gap-2 rounded-full bg-[var(--mt-paper-warm)] px-4 text-[13.5px] font-bold text-[var(--mt-ink-faint)]">
              <Phone className="h-4 w-4" strokeWidth={2.4} />
              No number
            </span>
          )}
          <Link
            to="/settings"
            className="flex h-11 items-center justify-center gap-2 rounded-full border-[1.5px] border-[var(--mt-leaf)]/25 bg-white px-4 text-[13.5px] font-bold text-[var(--mt-leaf-deep)]"
          >
            <Pencil className="h-4 w-4" strokeWidth={2.4} />
            Edit Profile
          </Link>
        </div>
      </motion.section>

      <StatStrip
        desktopColumnsClass="lg:grid-cols-4"
        items={[
          { label: "Your Farms", value: farms.length, icon: MapPin },
          { label: "Total Land", value: totalArea.toFixed(1), unit: "ac", icon: Hexagon },
          { label: "Plant Health", value: healthLabel, icon: Leaf },
          { label: "Last Check", value: lastCheck, icon: Calendar },
        ]}
      />

      {/* <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="overflow-hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white"
      >
        <div className="flex items-center justify-between px-5 py-4">
          <span className="flex items-center gap-2 text-[16px] font-extrabold text-[var(--mt-ink)]">
            <MapIcon className="h-[18px] w-[18px]" strokeWidth={2.1} />
            Farm Land Map
          </span>
          <span className="text-[12.5px] font-semibold text-[var(--mt-ink-soft)]">
            {farms.length === 1 ? "1 farm" : `${farms.length} farms`} &middot; Tap a pin to open
          </span>
        </div>
        <FarmerLandMap farms={farms} />
      </motion.div> */}

      <div className="overflow-hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white">
        <div className="flex items-center justify-between px-5 py-4">
          <span className="flex items-center gap-2 text-[16px] font-extrabold text-[var(--mt-ink)]">
            <MapPin className="h-[18px] w-[18px]" strokeWidth={2.1} />
            Farm Pointers
          </span>
          <span className="text-[12.5px] font-semibold text-[var(--mt-ink-soft)]">
            {farms.length === 1 ? "1 farm" : `${farms.length} farms`}
          </span>
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

      <div className="flex items-center justify-between pt-2">
        <h2 className="flex items-center gap-2 text-[17px] font-extrabold text-[var(--mt-ink)]">
          <MapPin className="h-[18px] w-[18px]" strokeWidth={2.1} />
          Your Farms
          <span className="rounded-full bg-[var(--mt-leaf-tint)] px-2.5 py-0.5 text-[12px] font-extrabold text-[var(--mt-leaf-deep)]">
            {farms.length}
          </span>
        </h2>
        <Link
          to="/farm-register"
          className="flex h-11 items-center gap-1.5 rounded-full bg-[var(--mt-leaf)] px-4 text-[13.5px] font-bold text-white"
        >
          <Plus className="h-4 w-4" strokeWidth={2.6} />
          Add Farm
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2 lg:grid-cols-3">
        {farms.map((farmItem, index) => (
          <motion.div
            key={farmItem.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
          >
            <FarmCard farm={farmItem} />
          </motion.div>
        ))}
      </div>
      {!loading && !error && farms.length === 0 && (
        <div className="rounded-[var(--mt-radius-md)] border border-dashed border-[var(--mt-line)] bg-white p-6 text-sm font-semibold text-[var(--mt-ink-soft)]">
          No farms are linked to you yet. Tap &ldquo;Add Farm&rdquo; to register your first one.
        </div>
      )}

      <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-5">
        <span className="mb-4 block text-[13px] font-extrabold text-[var(--mt-ink)]">Average Farm Health</span>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[13px]">
              <span className="flex items-center gap-1.5 font-bold text-[var(--mt-ink-soft)]">
                <Leaf className="h-4 w-4 text-[var(--mt-leaf)]" strokeWidth={2.4} />
                Green cover
              </span>
              <span className="font-extrabold text-[var(--mt-leaf-deep)]">{avgNdvi.toFixed(2)}</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-[var(--mt-paper-warm)]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(0, Math.min(100, avgNdvi * 100))}%` }}
                transition={{ duration: 1, delay: 0.3 }}
                className="h-full rounded-full bg-[var(--mt-leaf)]"
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[13px]">
              <span className="flex items-center gap-1.5 font-bold text-[var(--mt-ink-soft)]">
                <Droplets className="h-4 w-4 text-[var(--mt-sky-text)]" strokeWidth={2.4} />
                Soil water
              </span>
              <span className="font-extrabold text-[var(--mt-sky-text)]">{avgMoisture.toFixed(2)}</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-[var(--mt-paper-warm)]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(0, Math.min(100, avgMoisture * 100))}%` }}
                transition={{ duration: 1, delay: 0.5 }}
                className="h-full rounded-full bg-[var(--mt-sky)]"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-2">
        <h2 className="flex items-center gap-2 text-[17px] font-extrabold text-[var(--mt-ink)]">
          <Bell className="h-[18px] w-[18px]" strokeWidth={2.1} />
          Updates For You
        </h2>
        <span className="pulse-live h-2 w-2 rounded-full bg-[var(--mt-clay)]" />
      </div>
      <div className="rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-1.5">
        <NotificationStack limit={3} />
      </div>
    </div>
  );
}

