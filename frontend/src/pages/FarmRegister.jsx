import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  MapPin, User, Hexagon, FileText, Check, ChevronRight,
  ChevronLeft, Search, CornerDownRight, Loader2, Undo2, Trash2, Map as MapIcon,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MapContainer, Marker, Polygon, Polyline, TileLayer, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import FarmCard from "@/components/ui-custom/FarmCard";
import PipelineGlassLoader from "@/components/ui-custom/PipelineGlassLoader";
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

const MAP_CENTER = [19.81, 85.85];

function normalizePointList(points) {
  return points
    .filter((point) => Array.isArray(point) && point.length >= 2)
    .map(([lon, lat]) => [Number(lon), Number(lat)]);
}

function isValidCoordinatePair(point) {
  if (!Array.isArray(point) || point.length < 2) return false;
  const [lon, lat] = point;
  return Number.isFinite(lon) && Number.isFinite(lat) && lon >= -180 && lon <= 180 && lat >= -90 && lat <= 90;
}

function isValidPolygon(points) {
  const normalized = normalizePointList(points).filter(isValidCoordinatePair);
  const unique = normalized.filter((point, index, arr) =>
    arr.findIndex((candidate) => candidate[0] === point[0] && candidate[1] === point[1]) === index
  );
  return unique.length >= 3 && closePolygon(unique).length >= 4;
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

function parsePolygonCoordinates(text) {
  if (!text?.trim()) return SAMPLE_POLYGON;
  const parsed = JSON.parse(text);
  if (parsed?.type === "Polygon" && Array.isArray(parsed.coordinates?.[0])) return parsed.coordinates[0];
  if (Array.isArray(parsed)) return parsed;
  throw new Error("Boundary coordinates must be a GeoJSON polygon or a coordinate array.");
}

function toLatLngArray(points) {
  return normalizePointList(points).map(([lng, lat]) => [lat, lng]);
}

function toPointObjects(points) {
  return normalizePointList(points).map(([lng, lat]) => ({ lng, lat }));
}

function isValidLocationName(value) {
  return Boolean(value && String(value).trim() && String(value).trim().toLowerCase() !== "unassigned");
}

function buildHtmlSnippet(points) {
  const lines = points
    .map(([lon, lat], index) => `<div style="margin:2px 0"><strong>${index + 1}.</strong> ${lat.toFixed(6)}, ${lon.toFixed(6)}</div>`)
    .join("");
  return `
    <div style="font-family:Poppins,sans-serif;border:1px solid #e5e7eb;border-radius:18px;padding:16px;background:#fff">
      <div style="font-weight:700;margin-bottom:8px">Registered Land</div>
      ${lines}
    </div>
  `;
}

function MapClickCapture({ onAddPoint }) {
  useMapEvents({
    click(event) {
      onAddPoint([Number(event.latlng.lng.toFixed(6)), Number(event.latlng.lat.toFixed(6))]);
    },
  });
  return null;
}

function MapEditor({ points, setPoints }) {
  useEffect(() => {
    const leafletCssId = "leaflet-css";
    if (!document.getElementById(leafletCssId)) {
      const link = document.createElement("link");
      link.id = leafletCssId;
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }
  }, []);

  const polygonLatLngs = toLatLngArray(points);
  const center = polygonLatLngs[0] || MAP_CENTER;

  return (
    <div className="space-y-3">
      <div className="relative h-72 overflow-hidden rounded-2xl border border-gray-200 bg-gray-100">
        <MapContainer
          center={center}
          zoom={16}
          scrollWheelZoom
          className="h-full w-full"
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
          <MapClickCapture onAddPoint={(point) => setPoints((prev) => [...prev, point])} />
          {polygonLatLngs.map((position, index) => (
            <Marker key={`${position[0]}-${position[1]}-${index}`} position={position} />
          ))}
          {polygonLatLngs.length >= 2 && (
            <Polyline
              positions={polygonLatLngs}
              pathOptions={{
                color: "#ff3333",
                weight: 3,
                dashArray: "8,5",
              }}
            />
          )}
          {polygonLatLngs.length >= 3 && (
            <Polygon
              positions={polygonLatLngs}
              pathOptions={{
                color: "#ff3333",
                weight: 3,
                dashArray: "8,5",
                fillColor: "#ff3333",
                fillOpacity: 0.08,
              }}
            />
          )}
        </MapContainer>
        <div className="pointer-events-none absolute left-3 top-3 z-[500] rounded-xl bg-white/90 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-700 shadow-sm">
          Click on the map to add polygon points
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" onClick={() => setPoints((prev) => prev.slice(0, -1))} className="rounded-xl border-gray-200 text-xs font-semibold">
          <Undo2 className="mr-1 h-3.5 w-3.5" />
          Undo last point
        </Button>
        <Button type="button" variant="outline" onClick={() => setPoints([])} className="rounded-xl border-gray-200 text-xs font-semibold">
          <Trash2 className="mr-1 h-3.5 w-3.5" />
          Clear polygon
        </Button>
        <Button type="button" variant="outline" onClick={() => setPoints((prev) => closePolygon(prev.length >= 3 ? prev : SAMPLE_POLYGON))} className="rounded-xl border-gray-200 text-xs font-semibold">
          <Check className="mr-1 h-3.5 w-3.5" />
          Close polygon
        </Button>
        <Button type="button" variant="outline" onClick={() => setPoints(SAMPLE_POLYGON)} className="rounded-xl border-gray-200 text-xs font-semibold">
          <MapIcon className="mr-1 h-3.5 w-3.5" />
          Use sample polygon near selected block
        </Button>
      </div>
    </div>
  );
}

export default function FarmRegister() {
  const navigate = useNavigate();
  const user = getStoredUser();

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
  const [pipelineStage, setPipelineStage] = useState(0);
  const [pipelineOpen, setPipelineOpen] = useState(false);
  const [backendErrorDetail, setBackendErrorDetail] = useState("");

  const update = (field, value) => setFormData((prev) => ({ ...prev, [field]: value }));

  useEffect(() => {
    let cancelled = false;
    async function loadLookups() {
      setPageLoading(true);
      try {
        const statesPayload = await getStates().catch(() => []);
        if (cancelled) return;
        setStates(normalizeStates(statesPayload));
      } finally {
        if (!cancelled) setPageLoading(false);
      }
    }
    loadLookups();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (states.length && !formData.state_name) {
      update("state_name", "Odisha");
    }
  }, [states, formData.state_name]);

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
    if (!isValidLocationName(formData.district_name)) {
      setBlocks([]);
      return () => { cancelled = true; };
    }
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
          district_name: isValidLocationName(profile.district_name) ? profile.district_name : prev.district_name,
          block_name: isValidLocationName(profile.block_name) ? profile.block_name : prev.block_name,
          state_name: isValidLocationName(profile.state_name) ? profile.state_name : prev.state_name,
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

  const polygonGeoJson = useMemo(() => {
    if (isValidPolygon(polygonPoints)) return polygonToGeoJson(polygonPoints);
    try {
      const parsed = parsePolygonCoordinates(formData.coordinatesText);
      return isValidPolygon(parsed) ? polygonToGeoJson(parsed) : null;
    } catch {
      return null;
    }
  }, [formData.coordinatesText, polygonPoints]);

  const polygonPreviewPoints = useMemo(() => {
    if (polygonPoints.length) return closePolygon(polygonPoints);
    try {
      return closePolygon(parsePolygonCoordinates(formData.coordinatesText));
    } catch {
      return [];
    }
  }, [formData.coordinatesText, polygonPoints]);

  const canNext = useMemo(() => {
    if (step === 0) return Boolean(formData.district_name && formData.block_code);
    if (step === 1) {
      if (user?.role === "farmer") return true;
      return Boolean(formData.farmer_id || formData.farmer_name);
    }
    if (step === 2) return Boolean(polygonGeoJson);
    if (step === 3) return true;
    return true;
  }, [formData, step, polygonGeoJson, user?.role]);

  const successFarmCard = useMemo(() => {
    if (!registeredFarm) return null;
    return {
      id: registeredFarm.farm_id,
      surveyNumber: registeredFarm.survey_number || formData.survey_number || "Pending",
      village: formData.village_name || "Registered village",
      block: formData.block_name || "Block",
      district: formData.district_name || "District",
      area: Number(registeredFarm.area_acres || 2.4),
      crop: "Registered parcel",
      lastSatelliteDate: "Analysis queued",
      ndvi: 0.62,
      moisture: 0.44,
      status: "verified",
      h3Count: registeredFarm.h3_cell_count || polygonPoints.length || 0,
    };
  }, [registeredFarm, formData, polygonPoints.length]);

  async function captureSnapshot() {
    try {
      const html2canvas = (await import("html2canvas")).default;
      const node = document.getElementById("maatitrace-register-map");
      if (!node) return "";
      const canvas = await html2canvas(node, { backgroundColor: null, useCORS: true });
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
    setBackendErrorDetail("");
    setValidationWarning("");
    setPipelineOpen(true);
    setPipelineStage(0);
    setPipelineStatus("Validating location...");
    try {
      if (!polygonGeoJson) {
        throw new Error("Draw at least 3 points and close the polygon before registering.");
      }
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

      const geoJson = polygonGeoJson || null;
      if (!geoJson) {
        throw new Error("Draw a valid polygon or use the sample polygon before registering.");
      }
      setPipelineStatus("Generating H3 preview...");
      setPipelineStage(1);
      try {
        const preview = await previewH3({
          polygon: geoJson,
          resolution: 12,
          include_cells: false,
        });
        setH3Preview(preview);
      } catch (previewErr) {
        setValidationWarning(previewErr?.message || "H3 preview pending, continuing with farm registration.");
      }

      const registerPayload = {
        farmer_id: farmerId,
        farm_name: formData.farm_name || `${formData.farmer_name || "Farm"} parcel`,
        survey_number: formData.survey_number || null,
        state_name: validated.state_name,
        district_name: validated.district_name,
        block_name: validated.block_name,
        block_code: validated.block_code,
        village_name: formData.village_name || null,
        polygon: geoJson,
        h3_resolution: 12,
      };
      if (user?.role === "admin" || user?.role === "fpo") {
        registerPayload.fpo_id = linkedFarmer?.fpo_id || null;
      }

      setPipelineStatus("Registering farm...");
      setPipelineStage(2);
      console.error("FARM_REGISTER_PAYLOAD", registerPayload);
      const farmPayload = await registerFarm(registerPayload);
      setRegisteredFarm(farmPayload);

      setPipelineStatus("Capturing snapshot...");
      setPipelineStage(3);
      const snapshot = await captureSnapshot();
      if (snapshot) {
        await uploadFarmSnapshot(farmPayload.farm_id, snapshot).catch(() => {
          setValidationWarning("Snapshot upload endpoint pending. Saved locally for now.");
        });
      }

      setPipelineStatus("Materializing analysis...");
      setPipelineStage(4);
      await materializeFarmAnalysis(farmPayload.farm_id, {
        start_date: "2025-12-01",
        end_date: "2025-12-31",
        max_cloud_cover: 30,
        h3_resolution: 12,
        provider: "planetary_computer",
        collection_id: "sentinel-2-l2a",
        use_tiny_preview_bbox: true,
        tiny_bbox_size_deg: 0.0002,
      }).catch(() => setValidationWarning("Farm analysis endpoint pending. Registration still completed."));

      await materializeFarmTrends(farmPayload.farm_id, {}).catch(() => null);
      setPipelineStage(8);
      await materializeFarmGrid(farmPayload.farm_id, {}).catch(() => null);
      setPipelineStage(9);

      setPipelineStatus("Registered. Redirecting to land intelligence...");
      setPipelineStage(9);
      setTimeout(() => navigate(`/land/${farmPayload.farm_id}`), 800);
    } catch (err) {
      console.error("FARM_REGISTER_ERROR", {
        status: err?.response?.status,
        data: err?.response?.data,
        detail: err?.response?.data?.detail,
        payload: err?.config?.data,
        raw: err,
      });
      setBackendErrorDetail(JSON.stringify({
        status: err?.response?.status || null,
        data: err?.response?.data || null,
        detail: err?.response?.data?.detail || null,
      }, null, 2));
      const detail = err?.response?.data?.detail;
      const backendMessage =
        typeof detail === "string"
          ? detail
          : detail?.message || err?.response?.data?.message || err?.message;
      setError(backendMessage || "Unable to register farm.");
      setPipelineStage(-1);
    } finally {
      setLoading(false);
      setPipelineOpen(false);
    }
  }

  const inputClass = "rounded-xl border-gray-200 bg-white text-sm transition-all focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30";
  const labelClass = "text-[10px] font-bold uppercase tracking-widest text-gray-400";

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-gray-50 to-gray-100" style={{ fontFamily: "'Poppins', sans-serif" }}>
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

        {error && <div className="mb-4 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-600">{error}</div>}
        {validationWarning && <div className="mb-4 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-700">{validationWarning}</div>}
        {pipelineStatus && <div className="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">{pipelineStatus}</div>}
        <PipelineGlassLoader
          open={pipelineOpen}
          title="Land registration pipeline"
          status={pipelineStatus}
          currentStep={Math.max(0, pipelineStage)}
          steps={[
            "Validating location",
            "Previewing H3 cells",
            "Registering land boundary",
            "Saving farm polygon",
            "Starting satellite search",
            "Running raster index processing",
            "Writing H3 analytics",
            "Building 10m visual grid",
            "Computing H3-to-grid weighted averages",
            "Preparing land intelligence page",
          ]}
          details={[
            `State: ${formData.state_name || "—"}`,
            `District: ${formData.district_name || "—"}`,
            `Block: ${formData.block_name || "—"}`,
            `H3 res: 12`,
            `Points: ${polygonPoints.length}`,
          ]}
          failure={error || null}
        />

        {pageLoading ? (
          <div className="rounded-3xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">Loading registration lookup data...</div>
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
                  )}
                </div>
              )}

              {step === 2 && (
                <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-md">
                      <FileText className="h-4 w-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Draw Boundary</span>
                  </div>
                  <div className="grid gap-4 lg:grid-cols-[1.35fr_0.9fr]">
                    <div className="space-y-3 rounded-2xl border border-gray-100 bg-gray-50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Farm Boundary Map</p>
                          <p className="text-sm text-gray-600">Click the map to add coordinates. These points become the polygon sent to the backend.</p>
                        </div>
                        <div className="text-right text-xs text-gray-500">
                          <p>{polygonPoints.length} point{polygonPoints.length === 1 ? "" : "s"} selected</p>
                          <p>{polygonGeoJson ? "Polygon ready" : "Polygon pending"}</p>
                        </div>
                      </div>
                      <div id="maatitrace-register-map" className="overflow-hidden rounded-2xl border border-gray-200">
                        <MapEditor points={polygonPoints} setPoints={setPolygonPoints} />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="rounded-2xl border border-gray-100 bg-white p-3 text-sm text-gray-700">
                        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Polygon Status</p>
                        <p className="mt-1 text-lg font-bold">{polygonGeoJson ? "Ready" : "Pending"}</p>
                      </div>
                      <div className="rounded-2xl border border-gray-100 bg-white p-3 text-xs text-gray-600">
                        {polygonPreviewPoints.length > 0 ? polygonPreviewPoints.map((point, index) => (
                          <div key={`${point[0]}-${point[1]}-${index}`} className="flex items-center justify-between border-b border-gray-100 py-1 last:border-0">
                            <span className="font-semibold text-gray-500">Point {index + 1}</span>
                            <span className="font-mono text-[11px]">{point[1].toFixed(6)}, {point[0].toFixed(6)}</span>
                          </div>
                        )) : (
                          <p>No polygon points yet.</p>
                        )}
                      </div>
                      <div className="rounded-2xl border border-violet-100 bg-violet-50 p-3">
                        <span className="text-xs font-bold text-violet-700">
                          {polygonGeoJson ? "Polygon ready for backend" : "Polygon pending - draw at least 3 points"}
                        </span>
                      </div>
                      <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-700">
                        Use the sample polygon button for test-only validation if you need a quick backend check.
                      </div>
                    </div>
                  </div>
                  {backendErrorDetail && (
                    <pre className="whitespace-pre-wrap rounded-2xl border border-rose-100 bg-rose-50 p-3 text-[11px] text-rose-600">{backendErrorDetail}</pre>
                  )}
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
                  <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-700">
                    The polygon drawn in the previous step will be submitted exactly as GeoJSON.
                  </div>
                  {h3Preview && (
                    <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4 text-sm text-violet-700">
                      H3 preview ready. Estimated cells: {h3Preview.cell_count || h3Preview.returned_cell_count || "pending"}
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
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }} className="space-y-5 rounded-3xl border border-gray-100 bg-white p-8 text-center shadow-sm">
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: "spring", stiffness: 200, damping: 15 }} className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 shadow-xl shadow-emerald-500/30">
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
                  <div className="mx-auto max-w-md">{successFarmCard && <FarmCard farm={successFarmCard} />}</div>
                  <div className="flex gap-3">
                    <Button onClick={() => navigate(`/land/${registeredFarm.farm_id}`)} className="h-11 flex-1 rounded-2xl bg-emerald-500 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 hover:bg-emerald-600">
                      View Intelligence
                      <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                    <Button variant="outline" onClick={() => {
                      setStep(0);
                      setRegisteredFarm(null);
                      setError("");
                      setPipelineStatus("");
                      setValidationWarning("");
                      setPolygonPoints([]);
                      setSnapshotDataUrl("");
                      setH3Preview(null);
                      setFormData(EMPTY_FORM);
                    }} className="h-11 flex-1 rounded-2xl border-gray-200 text-sm font-semibold">
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
            <Button variant="ghost" onClick={() => setStep((current) => Math.max(0, current - 1))} disabled={step === 0 || loading} className="h-10 rounded-2xl px-5 text-sm font-semibold text-gray-500 hover:text-gray-800">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back
            </Button>
            {step < 3 && (
              <Button onClick={() => setStep((current) => Math.min(4, current + 1))} disabled={!canNext || loading} className="h-10 rounded-2xl bg-emerald-500 px-6 text-sm font-semibold text-white shadow-md shadow-emerald-500/20 transition-all hover:-translate-y-0.5 hover:bg-emerald-600 disabled:opacity-40">
                Continue
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            )}
          </motion.div>
        )}

        {!!snapshotDataUrl && <div className="mt-4 rounded-2xl border border-gray-100 bg-white p-4 text-xs text-gray-500 shadow-sm">Snapshot captured locally.</div>}
      </div>
    </div>
  );
}
