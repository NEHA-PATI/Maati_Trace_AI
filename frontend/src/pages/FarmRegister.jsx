import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCallback } from "react";
import {
  MapPin, User, Hexagon, FileText, Check, ChevronRight,
  ChevronLeft, Search,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import FarmCard from "@/components/ui-custom/FarmCard";
import HexagonPipelineLoader from "@/components/ui-custom/HexagonPipelineLoader";
import { getMyFarmerProfile } from "@/lib/api/farmer";
import { previewH3, registerFarm } from "@/lib/api/farm";
import { getCropProfiles } from "@/lib/api/analytics";
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
  runLatestAnalysis,
  getLatestAnalysisStatus,
  ANALYSIS_PIPELINE_STEPS,
} from "@/lib/api/hotStream";
import { getStoredUser } from "@/features/auth/session";
import FarmBoundaryStep from "@/features/farm-registration/boundary/FarmBoundaryStep";
import { resolveFarmLocation } from "@/features/farm-registration/boundary/locationGeocoder";
import { calculateBoundarySummary } from "@/features/farm-registration/boundary/boundaryUtils";

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
  crop_code: "",
  crop_variety: "",
  crop_stage: "",
  planting_date: "",
  runNow: true,
};
const FARM_DRAFT_KEY = "maatitrace:farm-registration:draft:v1";
const MotionDiv = motion.div;
const REGISTRATION_PIPELINE_STEPS = [
  "Validate farmer, crop and boundary",
  "Validate farm location",
  "Generate H3 hexagons",
  "Save farm record and polygon",
  "Start complete analysis",
];
const PIPELINE_STEPS = [
  ...REGISTRATION_PIPELINE_STEPS,
  ...ANALYSIS_PIPELINE_STEPS.map(([, label]) => label),
];

function isValidLocationName(value) {
  return Boolean(value && String(value).trim() && String(value).trim().toLowerCase() !== "unassigned");
}

function getAnalysisProgress(status, offset) {
  const terminal = ["completed", "completed_with_warnings", "failed"].includes(status?.status);
  if (terminal) {
    const finalStep = REGISTRATION_PIPELINE_STEPS.length + ANALYSIS_PIPELINE_STEPS.length - 1;
    return {
      step: finalStep,
      label: status.status === "failed" ? "Analysis failed" : "Build crop intelligence",
      status: status.status,
    };
  }
  const rows = Array.isArray(status?.stages) ? status.stages : [];
  const current = status?.current_stage;
  const index = ANALYSIS_PIPELINE_STEPS.findIndex(([key]) => key === current);
  let step = index >= 0 ? index : 0;
  let label = ANALYSIS_PIPELINE_STEPS[step]?.[1] || "Running analysis";
  const environment = rows.find((row) => row.name === "environment_datasets");
  const datasets = environment?.details?.datasets || [];
  if (current === "environment_datasets" && datasets.length) {
    const active = datasets.findIndex((row) => row.status === "running");
    const completed = datasets.filter((row) => ["succeeded", "cached", "completed_with_warnings"].includes(row.status)).length;
    const datasetIndex = active >= 0 ? active : Math.min(completed, ANALYSIS_PIPELINE_STEPS.length - 2);
    step = 1 + datasetIndex;
    label = ANALYSIS_PIPELINE_STEPS[step]?.[1] || label;
  }
  return { step: offset + step, label, status: status?.status || "running" };
}


export default function FarmRegister() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const pageRef = useRef(null);

  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [blocks, setBlocks] = useState([]);
  const [cropProfiles, setCropProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState("");
  const [pipelineStatus, setPipelineStatus] = useState("");
  const [registeredFarm, setRegisteredFarm] = useState(null);
  const [linkedFarmer, setLinkedFarmer] = useState(null);
  const [farmGeometry, setFarmGeometry] = useState(null);
  const [resolvedMapLocation, setResolvedMapLocation] = useState(null);
  const [locationResolving, setLocationResolving] = useState(false);
  const [locationResolutionError, setLocationResolutionError] = useState("");
  const [boundaryConfirmed, setBoundaryConfirmed] = useState(false);
  const [h3Preview, setH3Preview] = useState(null);
  const [validationWarning, setValidationWarning] = useState("");
  const [pipelineStage, setPipelineStage] = useState(0);
  const [pipelineOpen, setPipelineOpen] = useState(false);
  const [backendErrorDetail, setBackendErrorDetail] = useState("");

  const update = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (["state_name", "district_name", "block_code", "block_name", "village_name"].includes(field)) {
      setResolvedMapLocation(null);
      setLocationResolutionError("");
    }
  };

  useEffect(() => {
    try {
      const stored = localStorage.getItem(FARM_DRAFT_KEY);
      if (!stored) return;
      const draft = JSON.parse(stored);
      if (draft.formData) setFormData((current) => ({ ...current, ...draft.formData }));
      if (draft.farmGeometry) setFarmGeometry(draft.farmGeometry);
      if (draft.resolvedMapLocation) setResolvedMapLocation(draft.resolvedMapLocation);
    } catch {
      localStorage.removeItem(FARM_DRAFT_KEY);
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(FARM_DRAFT_KEY, JSON.stringify({
        formData,
        farmGeometry,
        resolvedMapLocation,
        savedAt: new Date().toISOString(),
      }));
    } catch {
      // Draft recovery is best-effort and must never block registration.
    }
  }, [farmGeometry, formData, resolvedMapLocation]);

  useEffect(() => {
    let cancelled = false;
    async function loadLookups() {
      setPageLoading(true);
      try {
        const [statesPayload, cropPayload] = await Promise.all([
          getStates().catch(() => []),
          getCropProfiles().catch(() => []),
        ]);
        if (cancelled) return;
        setStates(normalizeStates(statesPayload));
        setCropProfiles(Array.isArray(cropPayload) ? cropPayload : cropPayload?.items || []);
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

  const boundarySummary = useMemo(() => calculateBoundarySummary(farmGeometry), [farmGeometry]);

  const canNext = useMemo(() => {
    if (step === 0) return Boolean(formData.district_name && formData.block_code);
    if (step === 1) {
      if (!formData.crop_code) return false;
      if (user?.role === "farmer") {
        return Boolean(
          linkedFarmer?.farmer_id
          && linkedFarmer?.onboarding_status === "completed",
        );
      }
      return Boolean(formData.farmer_id);
    }
    if (step === 2) return boundarySummary.valid && boundaryConfirmed;
    if (step === 3) return true;
    return true;
  }, [formData, step, boundarySummary.valid, boundaryConfirmed, user?.role, linkedFarmer]);

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
      h3Count: registeredFarm.h3_cell_count || boundarySummary.pointCount || 0,
    };
  }, [registeredFarm, formData, boundarySummary.pointCount]);

  async function handleResolveSelectedLocation() {
    setLocationResolving(true);
    setLocationResolutionError("");
    try {
      const result = await resolveFarmLocation({
        state_name: formData.state_name,
        district_name: formData.district_name,
        block_name: selectedBlock?.block_name || formData.block_name,
        village_name: formData.village_name,
      });
      setResolvedMapLocation(result);
      return result;
    } catch (error) {
      setLocationResolutionError(error.message || "The selected location could not be found.");
      return null;
    } finally {
      setLocationResolving(false);
    }
  }

  async function handleNextStep() {
    if (step === 0) {
      const resolved = await handleResolveSelectedLocation();
      if (!resolved) {
        setError("We could not find the exact village. Continue and use your current location?");
      }
    }
    setStep((current) => Math.min(current + 1, 4));
  }

  const handleBoundaryGeometryChange = useCallback((geometry) => {
    setFarmGeometry(geometry);
    setBoundaryConfirmed(false);
    setH3Preview(null);
    setValidationWarning("");
  }, []);

  async function handleRegister() {
    let keepPipelineOpen = false;
    setLoading(true);
    setError("");
    setBackendErrorDetail("");
    setValidationWarning("");
    setPipelineOpen(true);
    setPipelineStage(0);
    setPipelineStatus("Validating location...");
    try {
      if (!boundarySummary.valid || !farmGeometry || !boundaryConfirmed) {
        throw new Error("Complete and confirm the farm boundary before registration.");
      }
      setPipelineStage(0);
      setPipelineStatus("Validating farm location...");
      setPipelineStage(1);
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
        throw new Error("Select an existing farmer profile before registering a farm.");
      }

      if (
        user?.role === "farmer"
        && linkedFarmer?.onboarding_status !== "completed"
      ) {
        throw new Error("Complete your farmer profile before registering a farm.");
      }

      setPipelineStatus("Generating H3 preview...");
      setPipelineStage(2);
      try {
        const preview = await previewH3({
          polygon: farmGeometry,
          include_cells: false,
          resolution: 12,
          max_cells: 20000,
        });
        setH3Preview(preview);
      } catch (previewErr) {
        setValidationWarning(previewErr?.message || "H3 preview pending, continuing with farm registration.");
      }

      const registerPayload = {
        farmer_id: farmerId,
        farm_name: formData.farm_name || `${formData.farmer_name || "Farm"} parcel`,
        survey_number: formData.survey_number || null,
        crop_code: formData.crop_code,
        crop_variety: formData.crop_variety || null,
        crop_stage: formData.crop_stage || null,
        planting_date: formData.planting_date || null,
        state_name: validated.state_name,
        district_name: validated.district_name,
        block_name: validated.block_name,
        block_code: validated.block_code,
        village_name: formData.village_name || null,
        polygon: farmGeometry,
        h3_resolution: 12,
      };

      setPipelineStatus("Saving farm record and polygon...");
      setPipelineStage(3);
      const farmPayload = await registerFarm(registerPayload);
      setRegisteredFarm(farmPayload);

      setPipelineStatus("Starting complete farm analysis...");
      setPipelineStage(4);
      const endDate = new Date();
      const startDate = new Date(endDate);
      startDate.setDate(startDate.getDate() - 365);
      await runLatestAnalysis(farmPayload.farm_id, {
        start_date: startDate.toISOString().slice(0, 10),
        end_date: endDate.toISOString().slice(0, 10),
        max_cloud_cover: 40,
        provider: "planetary_computer",
        collection_id: "sentinel-2-l2a",
      });

      let status = null;
      for (let attempt = 0; attempt < 300; attempt += 1) {
        status = await getLatestAnalysisStatus(farmPayload.farm_id);
        const progress = getAnalysisProgress(status, REGISTRATION_PIPELINE_STEPS.length);
        setPipelineStage(progress.step);
        setPipelineStatus(`${progress.label} · ${status.status || "running"}`);
        if (["completed", "completed_with_warnings", "failed"].includes(status.status)) break;
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
      }
      if (status?.status === "failed") {
        throw new Error(status.error_message || "Farm analysis failed.");
      }

      setPipelineStatus("Registered. Redirecting to land intelligence...");
      setPipelineStage(PIPELINE_STEPS.length - 1);
      keepPipelineOpen = true;
      localStorage.removeItem(FARM_DRAFT_KEY);
      setTimeout(() => navigate(`/land/${farmPayload.farm_id}`), 800);
    } catch (err) {
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
      if (!keepPipelineOpen) setPipelineOpen(false);
    }
  }

  const inputClass = "rounded-xl border-gray-200 bg-white text-sm transition-all focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30";
  const labelClass = "text-[10px] font-bold uppercase tracking-widest text-gray-400";

  return (
    <div ref={pageRef} className="flex min-h-screen bg-gradient-to-br from-gray-50 to-gray-100" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <div className={`mx-auto flex w-full flex-1 flex-col justify-center px-6 py-10 lg:px-12 ${step === 2 ? "max-w-[1600px]" : "max-w-2xl"}`}>
        <MotionDiv initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-emerald-500">Farm Registration</span>
          <h1 className="mt-1 text-3xl font-black text-gray-900">Register a Land Parcel</h1>
          <p className="mt-1 text-sm text-gray-400">Enter into the MaatiTrace satellite intelligence pipeline</p>
        </MotionDiv>

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
        {locationResolutionError && (
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-700">
            <span>{locationResolutionError} You can continue and use your current location.</span>
            <Button type="button" size="sm" variant="outline" onClick={() => { setError(""); setStep(1); }} className="h-9 rounded-xl border-amber-300 text-amber-800">
              Continue manually
            </Button>
          </div>
        )}
        {validationWarning && <div className="mb-4 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-700">{validationWarning}</div>}
        {pipelineStatus && <div className="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">{pipelineStatus}</div>}
        <HexagonPipelineLoader
          open={pipelineOpen}
          title="Land registration pipeline"
          status={pipelineStatus}
          currentStep={Math.max(0, pipelineStage)}
          steps={PIPELINE_STEPS}
          details={[
            `State: ${formData.state_name || "â€”"}`,
            `District: ${formData.district_name || "â€”"}`,
            `Block: ${formData.block_name || "â€”"}`,
            `Boundary: ${boundarySummary.valid ? `${boundarySummary.pointCount} corners` : "not completed"}`,
          ]}
          failure={error || null}
        />

        {pageLoading ? (
          <div className="rounded-3xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">Loading registration lookup data...</div>
        ) : (
          <AnimatePresence mode="wait">
            <MotionDiv
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
                  <div className="flex flex-wrap items-center gap-3 border-t border-gray-100 pt-4">
                    <Button type="button" variant="outline" onClick={handleResolveSelectedLocation} disabled={locationResolving} className="h-10 rounded-xl border-emerald-200 text-sm font-semibold text-emerald-700">
                      {locationResolving ? "Finding location…" : "Find village on map"}
                    </Button>
                    {resolvedMapLocation ? <span className="text-sm font-semibold text-emerald-700">Location found ({resolvedMapLocation.precision}).</span> : null}
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
                      <div className="space-y-1.5 sm:col-span-2">
                        <Label className={labelClass}>Crop grown on this farm <span className="text-rose-500">*</span></Label>
                        <Select value={formData.crop_code} onValueChange={(value) => update("crop_code", value)}>
                          <SelectTrigger className={inputClass}>
                            <SelectValue placeholder={cropProfiles.length ? "Select configured crop" : "No active crop profiles"} />
                          </SelectTrigger>
                          <SelectContent>
                            {cropProfiles.map((crop) => (
                              <SelectItem key={`${crop.crop_code}-${crop.profile_version}`} value={crop.crop_code}>
                                {crop.crop_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <p className="text-[10px] leading-4 text-slate-500">The crop selects this farm's active feature profile, temporal windows, formula versions, weights and thresholds. Admin-published crops appear here automatically.</p>
                      </div>
                      <div className="space-y-1.5">
                        <Label className={labelClass}>Variety <span className="text-slate-400">(optional)</span></Label>
                        <Input placeholder="Local cultivar / variety" value={formData.crop_variety} onChange={(e) => update("crop_variety", e.target.value)} className={inputClass} />
                      </div>
                      <div className="space-y-1.5">
                        <Label className={labelClass}>Growth stage <span className="text-slate-400">(optional)</span></Label>
                        <Input placeholder="e.g. vegetative / flowering" value={formData.crop_stage} onChange={(e) => update("crop_stage", e.target.value)} className={inputClass} />
                      </div>
                      <div className="space-y-1.5 sm:col-span-2">
                        <Label className={labelClass}>Planting date <span className="text-slate-400">(optional)</span></Label>
                        <Input type="date" value={formData.planting_date} onChange={(e) => update("planting_date", e.target.value)} className={inputClass} />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {step === 2 && (
                <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-4 shadow-sm sm:p-6">
                  <div className="mb-1 flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-md">
                      <Hexagon className="h-4 w-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Draw Boundary</span>
                  </div>
                  {resolvedMapLocation?.precision && resolvedMapLocation.precision !== "village" ? (
                    <p className="rounded-xl border border-amber-100 bg-amber-50 p-3 text-sm text-amber-800">
                      We found the {resolvedMapLocation.precision} location. Zoom in or use your current location to find the farm.
                    </p>
                  ) : null}
                  <FarmBoundaryStep
                    geometry={farmGeometry}
                    onGeometryChange={handleBoundaryGeometryChange}
                    resolvedLocation={resolvedMapLocation}
                    locationLabel={[formData.village_name, formData.block_name, formData.district_name].filter(Boolean).join(", ")}
                    onChangeLocation={() => setStep(0)}
                    onConfirm={() => {
                      if (!boundarySummary.valid) {
                        setError(boundarySummary.message);
                        return;
                      }
                      setBoundaryConfirmed(true);
                      setStep(3);
                    }}
                  />
                  {backendErrorDetail ? <pre className="whitespace-pre-wrap rounded-2xl border border-rose-100 bg-rose-50 p-3 text-[11px] text-rose-600">{backendErrorDetail}</pre> : null}
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
                      { label: "Boundary", value: boundarySummary.valid ? `${boundarySummary.acres.toFixed(2)} acre · ${boundarySummary.pointCount} corners` : "Pending" },
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
                  <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-sm font-semibold text-emerald-700">
                    Complete analysis is automatically included with every new farm registration. The results will open after processing finishes.
                  </div>
                  <Button onClick={handleRegister} disabled={loading} className="h-12 w-full rounded-2xl bg-emerald-500 text-sm font-bold text-white shadow-lg shadow-emerald-500/30 transition-all hover:-translate-y-0.5 hover:bg-emerald-600">
                    <Check className="mr-2 h-4 w-4" />
                    {loading ? "Registering..." : "Confirm & Register Farm"}
                  </Button>
                </div>
              )}

              {step === 4 && registeredFarm && (
                <MotionDiv initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }} className="space-y-5 rounded-3xl border border-gray-100 bg-white p-8 text-center shadow-sm">
                  <MotionDiv initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: "spring", stiffness: 200, damping: 15 }} className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 shadow-xl shadow-emerald-500/30">
                    <Check className="h-10 w-10 text-white" strokeWidth={3} />
                  </MotionDiv>
                  <div>
                    <h2 className="text-2xl font-black text-gray-900">Farm Registered!</h2>
                    <p className="mt-1 text-sm text-gray-400">Land registered. Analysis started or completed.</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-left">
                    {[
                      { label: "Farm ID", value: registeredFarm.farm_id },
                      { label: "Status", value: "Analysis completed" },
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
                      setFarmGeometry(null);
                      setBoundaryConfirmed(false);
                      setResolvedMapLocation(null);
                      setH3Preview(null);
                      setFormData(EMPTY_FORM);
                      localStorage.removeItem(FARM_DRAFT_KEY);
                    }} className="h-11 flex-1 rounded-2xl border-gray-200 text-sm font-semibold">
                      Register Another
                    </Button>
                  </div>
                </MotionDiv>
              )}
            </MotionDiv>
          </AnimatePresence>
        )}

        {step < 4 && (
          <MotionDiv initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 flex items-center justify-between">
            <Button variant="ghost" onClick={() => setStep((current) => Math.max(0, current - 1))} disabled={step === 0 || loading} className="h-10 rounded-2xl px-5 text-sm font-semibold text-gray-500 hover:text-gray-800">
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back
            </Button>
            {step < 3 && (
              <Button onClick={handleNextStep} disabled={!canNext || loading || locationResolving} className="h-10 rounded-2xl bg-emerald-500 px-6 text-sm font-semibold text-white shadow-md shadow-emerald-500/20 transition-all hover:-translate-y-0.5 hover:bg-emerald-600 disabled:opacity-40">
                Continue
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            )}
          </MotionDiv>
        )}

      </div>
    </div>
  );
}
