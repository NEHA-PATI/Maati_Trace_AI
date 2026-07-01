import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  MapPin, User, Hexagon, FileText, Check, ChevronRight,
  ChevronLeft, Search, Pencil, CornerDownRight, Loader2, Undo2, Trash2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import FarmCard from "@/components/ui-custom/FarmCard";
import { createFarmer, getMyFarmerProfile } from "@/lib/api/farmer";
import { previewH3, registerFarm, uploadFarmSnapshot } from "@/lib/api/farm";
import {
  getBlocks,
  getDistricts,
  getStates,
  normalizeBlocks,
  normalizeDistricts,
  normalizeStates,
  validateLocation,
} from "@/lib/api/location";
import {
  materializeFarmAnalysis,
  materializeFarmGrid,
  materializeFarmTrends,
} from "@/lib/api/hotStream";
import { getStoredUser } from "@/lib/auth/session";

const STEPS = [
  { num: "01", label: "Location", icon: MapPin },
  { num: "02", label: "Farmer", icon: User },
  { num: "03", label: "Boundary", icon: Hexagon },
  { num: "04", label: "Review", icon: FileText },
  { num: "05", label: "Done", icon: Check },
];

const BG_IMAGES = [
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/36_vcukad.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/34_sgalr8.jpg",
];

const EMPTY_FORM = {
  state_name: "Odisha",
  district_name: "",
  block_code: "",
  block_name: "",
  village_name: "",
  survey_number: "",
  farmer_id: "",
  farmer_name: "",
  farm_name: "",
  coordinatesText: "",
  runNow: true,
};

const SAMPLE_POLYGON = [
  [85.831, 19.814],
  [85.833, 19.814],
  [85.833, 19.816],
  [85.831, 19.816],
  [85.831, 19.814],
];

function ImagePanel({ step }) {
  const [loaded, setLoaded] = useState(false);
  return (
    <div className="relative h-full w-full overflow-hidden bg-gray-900">
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, scale: 1.06 }}
          animate={{ opacity: loaded ? 1 : 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.97 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="absolute inset-0"
        >
          {!loaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
              <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}>
                <Loader2 className="h-8 w-8 text-emerald-400/60" />
              </motion.div>
            </div>
          )}
          <img src={BG_IMAGES[step]} alt="" className="h-full w-full object-cover" onLoad={() => setLoaded(true)} onError={() => setLoaded(true)} />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/10" />
        </motion.div>
      </AnimatePresence>

      <div className="absolute bottom-8 left-8 right-8 z-10">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <span className="text-[10px] uppercase tracking-[0.3em] text-white/50">Step {STEPS[step]?.num}</span>
          <h3 className="mt-1 text-2xl font-black text-white" style={{ fontFamily: "'Poppins', sans-serif" }}>{STEPS[step]?.label}</h3>
          <div className="mt-3 flex gap-1">
            {STEPS.map((_, index) => (
              <motion.div
                key={index}
                animate={{ width: index === step ? 24 : 6 }}
                transition={{ duration: 0.3 }}
                className={`h-1 rounded-full ${index === step ? "bg-emerald-400" : index < step ? "bg-emerald-400/50" : "bg-white/20"}`}
              />
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function parsePolygonCoordinates(text) {
  if (!text?.trim()) {
    return SAMPLE_POLYGON;
  }
  const parsed = JSON.parse(text);
  if (parsed?.type === "Polygon" && Array.isArray(parsed.coordinates?.[0])) return parsed.coordinates[0];
  if (Array.isArray(parsed)) return parsed;
  throw new Error("Boundary coordinates must be a GeoJSON polygon or a coordinate array.");
}

function normalizePointList(points) {
  return points
    .filter((point) => Array.isArray(point) && point.length >= 2)
    .map(([lon, lat]) => [Number(lon), Number(lat)]);
}

function closePolygon(points) {
  const normalized = normalizePointList(points);
  if (normalized.length < 3) return normalized;
  const [firstLon, firstLat] = normalized[0];
  const [lastLon, lastLat] = normalized[normalized.length - 1];
  if (firstLon === lastLon && firstLat === lastLat) return normalized;
  return [...normalized, [firstLon, firstLat]];
}

function polygonToGeoJson(points) {
  return {
    type: "Polygon",
    coordinates: [closePolygon(points)],
  };
}

function toPointFromClick(event, container) {
  const rect = container.getBoundingClientRect();
  const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
  const y = Math.max(0, Math.min(rect.height, event.clientY - rect.top));
  const lon = 85.80 + (x / rect.width) * 0.08;
  const lat = 19.79 + (1 - y / rect.height) * 0.05;
  return [Number(lon.toFixed(6)), Number(lat.toFixed(6))];
}

function MapEditor({ polygonPoints, setPolygonPoints, containerRef }) {
  const onMapClick = (event) => {
    if (!containerRef.current) return;
    const point = toPointFromClick(event, containerRef.current);
    setPolygonPoints((prev) => [...prev, point]);
  };

  const svgPoints = polygonPoints.map(([lon, lat]) => {
    const x = ((lon - 85.80) / 0.08) * 100;
    const y = (1 - (lat - 19.79) / 0.05) * 100;
    return `${x}%,${y}%`;
  });

  return (
    <div
      ref={containerRef}
      onClick={onMapClick}
      className="relative h-64 cursor-crosshair overflow-hidden rounded-2xl border border-gray-200 bg-gray-100"
    >
      <img src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg" alt="" className="h-full w-full object-cover opacity-45" />
      <svg className="absolute inset-0 h-full w-full">
        {svgPoints.length >= 2 && (
          <polyline
            points={svgPoints.join(" ")}
            fill="rgba(220,38,38,0.08)"
            stroke="#ff3333"
            strokeWidth="3"
            strokeDasharray="8,5"
            strokeLinejoin="round"
          />
        )}
        {polygonPoints.map(([lon, lat], index) => {
          const x = ((lon - 85.80) / 0.08) * 100;
          const y = (1 - (lat - 19.79) / 0.05) * 100;
          return (
            <g key={`${lon}-${lat}-${index}`}>
              <circle cx={`${x}%`} cy={`${y}%`} r="10" fill="#16a34a" opacity="0.18" />
              <circle cx={`${x}%`} cy={`${y}%`} r="5" fill="#16a34a" />
              <text x={`${x}%`} y={`calc(${y}% - 10px)`} textAnchor="middle" fontSize="12" fontWeight="700" fill="#166534">
                {index + 1}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="absolute left-3 top-3 flex gap-2">
        <button type="button" className="rounded-xl bg-white/90 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-700 shadow-sm">
          Click to add points
        </button>
      </div>
      <div className="absolute bottom-3 right-3 flex flex-col gap-1">
        <button type="button" className="flex h-7 w-7 items-center justify-center rounded-md bg-gray-900/80 text-lg font-bold leading-none text-white transition-colors hover:bg-gray-800">
          +
        </button>
        <button type="button" className="flex h-7 w-7 items-center justify-center rounded-md bg-gray-900/80 text-lg font-bold leading-none text-white transition-colors hover:bg-gray-800">
          -
        </button>
      </div>
    </div>
  );
}

export default function FarmRegister() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const mapRef = useRef(null);

  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [blocks, setBlocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");
  const [pipelineStatus, setPipelineStatus] = useState("");
  const [registeredFarm, setRegisteredFarm] = useState(null);
  const [linkedFarmer, setLinkedFarmer] = useState(null);
  const [polygonPoints, setPolygonPoints] = useState([]);
  const [snapshotDataUrl, setSnapshotDataUrl] = useState("");
  const [h3Preview, setH3Preview] = useState(null);
  const [validationWarning, setValidationWarning] = useState("");

  const update = (field, value) => setFormData((prev) => ({ ...prev, [field]: value }));

  useEffect(() => {
    let cancelled = false;
    async function loadLookups() {
      setPageLoading(true);
      try {
        const statesPayload = await getStates().catch(() => []);
        if (cancelled) return;
        setStates(normalizeStates(statesPayload));
        update("state_name", "Odisha");
      } finally {
        if (!cancelled) setPageLoading(false);
      }
    }
    loadLookups();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (!formData.state_name) return;
    getDistricts(formData.state_name)
      .then((payload) => {
        if (cancelled) return;
        setDistricts(normalizeDistricts(payload));
      })
      .catch(() => setDistricts([]));
    return () => { cancelled = true; };
  }, [formData.state_name]);

  useEffect(() => {
    let cancelled = false;
    if (!formData.state_name || !formData.district_name) return;
    getBlocks(formData.state_name, formData.district_name)
      .then((payload) => {
        if (cancelled) return;
        setBlocks(normalizeBlocks(payload));
      })
      .catch(() => setBlocks([]));
    return () => { cancelled = true; };
  }, [formData.state_name, formData.district_name]);

  useEffect(() => {
    let cancelled = false;
    if (user?.role !== "farmer") return;
    getMyFarmerProfile()
      .then((profile) => {
        if (cancelled) return;
        setLinkedFarmer(profile);
        setFormData((prev) => ({
          ...prev,
          farmer_id: profile.farmer_id,
          farmer_name: profile.full_name || prev.farmer_name,
          district_name: profile.district_name || prev.district_name,
          block_name: profile.block_name || prev.block_name,
          state_name: profile.state_name || prev.state_name,
          village_name: profile.village_name || prev.village_name,
        }));
      })
      .catch(() => {
        if (cancelled) return;
        setLinkedFarmer(null);
      });
    return () => { cancelled = true; };
  }, [user?.role]);

  const selectedBlock = useMemo(
    () => blocks.find((block) => String(block.block_code) === String(formData.block_code)) || null,
    [blocks, formData.block_code],
  );

  const canNext = useMemo(() => {
    if (step === 0) return Boolean(formData.district_name && formData.block_code);
    if (step === 1) {
      if (user?.role === "farmer") return true;
      return Boolean(formData.farmer_id || formData.farmer_name);
    }
    if (step === 2) return polygonPoints.length >= 3 || formData.coordinatesText.trim().length > 0;
    return true;
  }, [formData, step, polygonPoints.length, user?.role]);

  const polygonGeoJson = useMemo(() => {
    if (polygonPoints.length >= 3) return polygonToGeoJson(polygonPoints);
    try {
      const fallback = parsePolygonCoordinates(formData.coordinatesText);
      return polygonToGeoJson(fallback);
    } catch {
      return null;
    }
  }, [formData.coordinatesText, polygonPoints]);

  const successFarmCard = useMemo(() => {
    if (!registeredFarm) return null;
    return {
      id: registeredFarm.farm_id,
      surveyNumber: registeredFarm.survey_number || formData.survey_number || "Pending",
      village: formData.village_name || "Registered village",
      block: formData.block_name || "Block",
      district: formData.district_name || "District",
      area: Number(registeredFarm.area_acres || formData.area || 2.4),
      crop: "Registered parcel",
      lastSatelliteDate: "Analysis queued",
      ndvi: 0.62,
      moisture: 0.44,
      status: "verified",
      h3Count: registeredFarm.h3_cell_count || polygonPoints.length || 0,
    };
  }, [registeredFarm, formData, polygonPoints.length]);

  async function captureSnapshot() {
    if (!mapRef.current) return "";
    try {
      const html2canvas = (await import("html2canvas")).default;
      const canvas = await html2canvas(mapRef.current, { backgroundColor: null, useCORS: true });
      const dataUrl = canvas.toDataURL("image/png");
      setSnapshotDataUrl(dataUrl);
      return dataUrl;
    } catch {
      return "";
    }
  }

  async function handleRegister() {
    setLoading(true);
    setError("");
    setValidationWarning("");
    setPipelineStatus("Validating location...");
    try {
      const validated = await validateLocation({
        state_name: formData.state_name,
        district_name: formData.district_name,
        block_name: selectedBlock?.block_name || formData.block_name,
        block_code: Number(formData.block_code),
      });

      let farmerId = formData.farmer_id || linkedFarmer?.farmer_id;
      if (!farmerId) {
        if (user?.role === "farmer") {
          throw new Error("Complete your farmer profile first");
        }
        const farmerPayload = await createFarmer({
          user_id: null,
          full_name: formData.farmer_name,
          state_name: validated.state_name,
          district_name: validated.district_name,
          block_name: validated.block_name,
          block_code: validated.block_code,
          village_name: formData.village_name || null,
          phone_number: user?.phone_number || null,
        });
        farmerId = farmerPayload.farmer_id;
        setLinkedFarmer(farmerPayload);
      }

      const geoJson = polygonGeoJson || polygonToGeoJson(SAMPLE_POLYGON);
      const previewPayload = {
        polygon: geoJson,
        h3_resolution: 12,
        use_tiny_preview_bbox: true,
      };

      setPipelineStatus("Generating H3 preview...");
      try {
        const preview = await previewH3(previewPayload);
        setH3Preview(preview);
      } catch (previewErr) {
        setValidationWarning(previewErr?.message || "H3 preview pending, continuing with farm registration.");
      }

      setPipelineStatus("Registering farm...");
      const farmPayload = await registerFarm({
        farmer_id: farmerId,
        fpo_id: user?.role === "admin" || user?.role === "fpo" ? linkedFarmer?.fpo_id || null : linkedFarmer?.fpo_id || null,
        farm_name: formData.farm_name || `${formData.farmer_name || "Farm"} parcel`,
        survey_number: formData.survey_number || null,
        state_name: validated.state_name,
        district_name: validated.district_name,
        block_name: validated.block_name,
        block_code: validated.block_code,
        village_name: formData.village_name || null,
        polygon_geojson: geoJson,
        h3_resolution: 12,
      });

      setRegisteredFarm(farmPayload);

      setPipelineStatus("Capturing snapshot...");
      const snapshot = await captureSnapshot();
      if (snapshot) {
        await uploadFarmSnapshot(farmPayload.farm_id, snapshot).catch(() => {
          setValidationWarning("Snapshot upload endpoint pending. Saved locally for now.");
        });
      }

      setPipelineStatus("Materializing analysis...");
      await materializeFarmAnalysis(farmPayload.farm_id, {
        start_date: "2025-12-01",
        end_date: "2025-12-31",
        max_cloud_cover: 30,
        h3_resolution: 12,
        provider: "planetary_computer",
        collection_id: "sentinel-2-l2a",
        use_tiny_preview_bbox: true,
        tiny_bbox_size_deg: 0.0002,
      }).catch(() => {
        setValidationWarning("Farm analysis endpoint pending. Registration still completed.");
      });

      await materializeFarmTrends(farmPayload.farm_id, {}).catch(() => null);
      await materializeFarmGrid(farmPayload.farm_id, {}).catch(() => null);

      setPipelineStatus("Registered. Redirecting to land intelligence...");
      setTimeout(() => navigate(`/land/${farmPayload.farm_id}`), 800);
    } catch (err) {
      setError(typeof err?.message === "string" ? err.message : "Unable to register farm.");
    } finally {
      setLoading(false);
    }
  }

  const inputClass = "rounded-xl border-gray-200 bg-white text-sm transition-all focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30";
  const labelClass = "text-[10px] font-bold uppercase tracking-widest text-gray-400";

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-gray-50 to-gray-100" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <div className="sticky top-0 hidden h-screen w-2/5 lg:block">
        <ImagePanel step={Math.min(step, 4)} />
      </div>

      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-6 py-10 lg:px-12">
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-emerald-500">Farm Registration</span>
          <h1 className="mt-1 text-3xl font-black text-gray-900">Register a Land Parcel</h1>
          <p className="mt-1 text-sm text-gray-400">Enter into the MaatiTrace satellite intelligence pipeline</p>
        </motion.div>

        <div className="mb-8 flex gap-2 overflow-x-auto pb-1">
          {STEPS.map((item, index) => {
            const Icon = item.icon;
            const isActive = index === step;
            const isDone = index < step;
            return (
              <button
                key={item.num}
                onClick={() => index <= step && setStep(index)}
                className={`whitespace-nowrap rounded-2xl px-3 py-2 text-xs font-semibold transition-all ${
                  isActive ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30" :
                  isDone ? "border border-emerald-200 bg-emerald-50 text-emerald-600" :
                  "border border-gray-200 bg-white text-gray-400"
                }`}
              >
                <span className="flex items-center gap-1.5">
                  {isDone ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
                  <span className="hidden sm:inline">{item.label}</span>
                </span>
              </button>
            );
          })}
        </div>

        {error && (
          <div className="mb-4 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-600">
            {error}
          </div>
        )}

        {validationWarning && (
          <div className="mb-4 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-700">
            {validationWarning}
          </div>
        )}

        {pipelineStatus && (
          <div className="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">
            {pipelineStatus}
          </div>
        )}

        {pageLoading ? (
          <div className="rounded-3xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">
            Loading registration lookup data...
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              {step === 0 && (
                <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 shadow-md">
                      <MapPin className="h-4 w-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Location Selection</span>
                  </div>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label className={labelClass}>State</Label>
                      <Select value={formData.state_name} onValueChange={(value) => update("state_name", value)}>
                        <SelectTrigger className={inputClass}><SelectValue placeholder="Select state" /></SelectTrigger>
                        <SelectContent>
                          {(states.length ? states : [{ state_name: "Odisha" }]).map((state) => (
                            <SelectItem key={state.state_name} value={state.state_name}>{state.state_name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>District</Label>
                      <Select value={formData.district_name} onValueChange={(value) => update("district_name", value)}>
                        <SelectTrigger className={inputClass}><SelectValue placeholder="Select district" /></SelectTrigger>
                        <SelectContent>
                          {districts.map((district) => (
                            <SelectItem key={`${district.district_code}-${district.district_name}`} value={district.district_name}>
                              {district.district_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>Block</Label>
                      <Select
                        value={String(formData.block_code || "")}
                        onValueChange={(value) => {
                          const selected = blocks.find((block) => String(block.block_code) === String(value));
                          update("block_code", selected?.block_code ?? value);
                          update("block_name", selected?.block_name ?? "");
                        }}
                      >
                        <SelectTrigger className={inputClass}>
                          <SelectValue placeholder="Select block">
                            {formData.block_name ? `${formData.block_name} (${formData.block_code})` : "Select block"}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {blocks.map((block) => (
                            <SelectItem key={block.block_code} value={String(block.block_code)}>
                              {block.block_name} ({block.block_code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>Village</Label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
                        <Input placeholder="Village name..." value={formData.village_name} onChange={(e) => update("village_name", e.target.value)} className={`${inputClass} pl-9`} />
                      </div>
                    </div>
                  </div>
                  <div className="relative h-48 overflow-hidden rounded-2xl border border-gray-200 bg-gray-100">
                    <img src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg" alt="" className="h-full w-full object-cover opacity-40" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <MapPin className="mx-auto mb-2 h-8 w-8 text-emerald-500" strokeWidth={2} />
                        <p className="text-xs font-medium text-gray-500">
                          {formData.district_name && formData.block_name ? `${formData.block_name}, ${formData.district_name}` : "Select district and block to load map"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {step === 1 && (
                <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-500 shadow-md">
                      <User className="h-4 w-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Farmer Linkage</span>
                  </div>
                  {user?.role === "farmer" && !linkedFarmer ? (
                    <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-700">
                      Complete your farmer profile first.
                      <div className="mt-3">
                        <Link to="/farmer/me" className="inline-flex">
                          <Button size="sm" className="h-9 rounded-xl bg-amber-500 text-white hover:bg-amber-600">Go to Farmer Profile</Button>
                        </Link>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50 p-3">
                        <CornerDownRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-400" />
                        <span className="text-xs text-blue-600">Link this farm to an existing farmer or create a new record.</span>
                      </div>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div className="space-y-1.5">
                          <Label className={labelClass}>Farmer Name</Label>
                          <Input placeholder="Enter full name..." value={formData.farmer_name} onChange={(e) => update("farmer_name", e.target.value)} className={inputClass} disabled={user?.role === "farmer"} />
                        </div>
                        <div className="space-y-1.5">
                          <Label className={labelClass}>Farmer ID</Label>
                          <Input placeholder="Paste existing farmer ID" value={formData.farmer_id} onChange={(e) => update("farmer_id", e.target.value)} className={inputClass} disabled={user?.role === "farmer"} />
                        </div>
                        <div className="space-y-1.5 sm:col-span-2">
                          <Label className={labelClass}>Farm Name</Label>
                          <Input placeholder="Farm name" value={formData.farm_name} onChange={(e) => update("farm_name", e.target.value)} className={inputClass} />
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {step === 2 && (
                <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-400 to-purple-500 shadow-md">
                      <Hexagon className="h-4 w-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Farm Boundary</span>
                  </div>
                  <div className="space-y-3">
                    <div className="relative" ref={mapRef}>
                      <MapEditor polygonPoints={polygonPoints} setPolygonPoints={setPolygonPoints} containerRef={mapRef} />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" variant="outline" onClick={() => setPolygonPoints((prev) => prev.slice(0, -1))} className="rounded-xl border-gray-200 text-xs font-semibold">
                        <Undo2 className="mr-1 h-3.5 w-3.5" />
                        Undo last point
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setPolygonPoints([])} className="rounded-xl border-gray-200 text-xs font-semibold">
                        <Trash2 className="mr-1 h-3.5 w-3.5" />
                        Clear polygon
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setPolygonPoints(SAMPLE_POLYGON)} className="rounded-xl border-gray-200 text-xs font-semibold">
                        Use sample farm polygon
                      </Button>
                    </div>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <div className="space-y-1.5">
                        <Label className={labelClass}>Polygon GeoJSON</Label>
                        <Textarea
                          placeholder='{"type":"Polygon","coordinates":[[[85.831,19.814],[85.833,19.814],[85.833,19.816],[85.831,19.816],[85.831,19.814]]]}'
                          value={formData.coordinatesText}
                          onChange={(e) => update("coordinatesText", e.target.value)}
                          rows={5}
                          className={`${inputClass} font-mono text-xs`}
                        />
                      </div>
                      <div className="space-y-3">
                        <div className="rounded-2xl border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Polygon Points</p>
                          <p className="mt-1 text-lg font-bold">{polygonPoints.length}</p>
                        </div>
                        {polygonGeoJson && (
                          <div className="rounded-2xl border border-violet-100 bg-violet-50 p-3">
                            <span className="text-xs font-bold text-violet-700">Polygon ready for backend</span>
                          </div>
                        )}
                        {formData.area && (
                          <div className="rounded-2xl border border-violet-100 bg-violet-50 p-3">
                            <span className="text-xs font-bold text-violet-700">Estimated Area</span>
                            <p className="text-[10px] text-violet-500">Approx. {Math.ceil(parseFloat(formData.area || 0) * 7.5)} cells at current resolution</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-md">
                      <FileText className="h-4 w-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Review & Confirm</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "State", value: formData.state_name },
                      { label: "District", value: formData.district_name || "-" },
                      { label: "Block", value: formData.block_name || "-" },
                      { label: "Farmer", value: formData.farmer_name || linkedFarmer?.full_name || "-" },
                      { label: "Farmer ID", value: formData.farmer_id || linkedFarmer?.farmer_id || "New" },
                      { label: "Survey No.", value: formData.survey_number || "-" },
                      { label: "Village", value: formData.village_name || "-" },
                      { label: "Polygon Points", value: polygonPoints.length || "GeoJSON" },
                    ].map((item) => (
                      <div key={item.label} className="rounded-2xl border border-gray-100 bg-gray-50 p-3">
                        <span className="mb-1 block text-[9px] font-bold uppercase tracking-widest text-gray-400">{item.label}</span>
                        <span className="text-sm font-bold text-gray-800">{item.value}</span>
                      </div>
                    ))}
                  </div>
                  {h3Preview && (
                    <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4 text-sm text-violet-700">
                      H3 preview ready.
                    </div>
                  )}
                  <label className="flex items-center gap-2 text-sm text-gray-600">
                    <input type="checkbox" checked={formData.runNow} onChange={(e) => update("runNow", e.target.checked)} />
                    Run latest analysis after registration
                  </label>
                  <Button onClick={handleRegister} disabled={loading} className="h-12 w-full rounded-2xl bg-emerald-500 text-sm font-bold text-white shadow-lg shadow-emerald-500/30 transition-all hover:-translate-y-0.5 hover:bg-emerald-600">
                    <Check className="mr-2 h-4 w-4" />
                    {loading ? "Registering..." : "Confirm & Register Farm"}
                  </Button>
                </div>
              )}

              {step === 4 && registeredFarm && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="space-y-5 rounded-3xl border border-gray-100 bg-white p-8 text-center shadow-sm"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 200, damping: 15 }}
                    className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 shadow-xl shadow-emerald-500/30"
                  >
                    <Check className="h-10 w-10 text-white" strokeWidth={3} />
                  </motion.div>
                  <div>
                    <h2 className="text-2xl font-black text-gray-900">Farm Registered!</h2>
                    <p className="mt-1 text-sm text-gray-400">Land registered. Analysis started or completed.</p>
                  </div>
                <div className="grid grid-cols-2 gap-3 text-left">
                    {[
                      { label: "Farm ID", value: registeredFarm.farm_id },
                      { label: "Status", value: formData.runNow ? "Analysis requested" : "Registered" },
                      { label: "Survey Number", value: registeredFarm.survey_number || "Pending" },
                      { label: "H3 Cells", value: `${registeredFarm.h3_cell_count || 0} generated` },
                    ].map((item) => (
                      <div key={item.label} className="rounded-2xl border border-emerald-100 bg-emerald-50 p-3">
                        <span className="mb-0.5 block text-[9px] font-bold uppercase tracking-widest text-emerald-400">{item.label}</span>
                        <span className="text-sm font-bold text-gray-800">{item.value}</span>
                      </div>
                    ))}
                </div>
                  <div className="mx-auto max-w-md">
                    {successFarmCard && <FarmCard farm={successFarmCard} />}
                  </div>
                  <div className="flex gap-3">
                    <Button onClick={() => navigate(`/land/${registeredFarm.farm_id}`)} className="h-11 flex-1 rounded-2xl bg-emerald-500 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 hover:bg-emerald-600">
                      View Intelligence
                      <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setStep(0);
                        setRegisteredFarm(null);
                        setError("");
                        setPipelineStatus("");
                        setValidationWarning("");
                        setPolygonPoints([]);
                        setSnapshotDataUrl("");
                        setH3Preview(null);
                        setFormData(EMPTY_FORM);
                      }}
                      className="h-11 flex-1 rounded-2xl border-gray-200 text-sm font-semibold"
                    >
                      Register Another
                    </Button>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </AnimatePresence>
        )}

        {step < 4 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={() => setStep((current) => Math.max(0, current - 1))}
              disabled={step === 0 || loading}
              className="h-10 rounded-2xl px-5 text-sm font-semibold text-gray-500 hover:text-gray-800"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back
            </Button>
            {step < 3 && (
              <Button
                onClick={() => setStep((current) => Math.min(4, current + 1))}
                disabled={!canNext || loading}
                className="h-10 rounded-2xl bg-emerald-500 px-6 text-sm font-semibold text-white shadow-md shadow-emerald-500/20 transition-all hover:-translate-y-0.5 hover:bg-emerald-600 disabled:opacity-40"
              >
                Continue
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            )}
          </motion.div>
        )}

        {!!snapshotDataUrl && (
          <div className="mt-4 rounded-2xl border border-gray-100 bg-white p-4 text-xs text-gray-500 shadow-sm">
            Snapshot captured locally.
          </div>
        )}
      </div>
    </div>
  );
}
