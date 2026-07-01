import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  MapPin, User, Hexagon, FileText, Check, ChevronRight,
  ChevronLeft, Search, Pencil, CornerDownRight, Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { motion, AnimatePresence } from "framer-motion";

const STEPS = [
  { num: "01", label: "Location", icon: MapPin, color: "from-emerald-400 to-teal-500" },
  { num: "02", label: "Farmer", icon: User, color: "from-blue-400 to-indigo-500" },
  { num: "03", label: "Boundary", icon: Hexagon, color: "from-violet-400 to-purple-500" },
  { num: "04", label: "Review", icon: FileText, color: "from-amber-400 to-orange-500" },
  { num: "05", label: "Done", icon: Check, color: "from-emerald-400 to-green-500" },
];

const BG_IMAGES = [
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/36_vcukad.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/34_sgalr8.jpg",
];

function ImagePanel({ step }) {
  const [loaded, setLoaded] = useState(false);
  return (
    <div className="relative w-full h-full overflow-hidden bg-gray-900">
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
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
              >
                <Loader2 className="w-8 h-8 text-emerald-400/60" />
              </motion.div>
            </div>
          )}
          <img
            src={BG_IMAGES[step]}
            alt=""
            className="w-full h-full object-cover"
            onLoad={() => setLoaded(true)}
            onError={() => setLoaded(true)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/10" />
        </motion.div>
      </AnimatePresence>

      {/* Step label overlay */}
      <div className="absolute bottom-8 left-8 right-8 z-10">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <span className="text-[10px] uppercase tracking-[0.3em] text-white/50">Step {STEPS[step]?.num}</span>
          <h3 className="text-2xl font-black text-white mt-1" style={{ fontFamily: "'Poppins', sans-serif" }}>
            {STEPS[step]?.label}
          </h3>
          <div className="flex gap-1 mt-3">
            {STEPS.map((_, i) => (
              <motion.div
                key={i}
                animate={{ width: i === step ? 24 : 6 }}
                transition={{ duration: 0.3 }}
                className={`h-1 rounded-full ${i === step ? "bg-emerald-400" : i < step ? "bg-emerald-400/50" : "bg-white/20"}`}
              />
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default function FarmRegister() {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    state: "Odisha", district: "", block: "", village: "",
    surveyNumber: "", farmerId: "", farmerName: "", coordinates: "", area: "",
  });
  const [registered, setRegistered] = useState(false);

  const update = (field, val) => setFormData(p => ({ ...p, [field]: val }));

  const canNext = () => {
    if (step === 0) return formData.district && formData.block;
    if (step === 1) return formData.farmerName;
    if (step === 2) return formData.coordinates || formData.area;
    return true;
  };

  const handleRegister = () => { setRegistered(true); setStep(4); };

  const inputClass = "bg-white border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-400/30 focus:border-emerald-400 transition-all";
  const labelClass = "text-[10px] font-bold uppercase tracking-widest text-gray-400";

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex" style={{ fontFamily: "'Poppins', sans-serif" }}>
      {/* Left — Image Panel */}
      <div className="hidden lg:block w-2/5 h-screen sticky top-0">
        <ImagePanel step={Math.min(step, 4)} />
      </div>

      {/* Right — Form */}
      <div className="flex-1 flex flex-col justify-center py-10 px-6 lg:px-12 max-w-2xl mx-auto w-full">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <span className="text-[10px] uppercase tracking-[0.3em] text-emerald-500 font-bold">Farm Registration</span>
          <h1 className="text-3xl font-black text-gray-900 mt-1">Register a Land Parcel</h1>
          <p className="text-sm text-gray-400 mt-1">Enter into the MaatiTrace satellite intelligence pipeline</p>
        </motion.div>

        {/* Step tabs */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-1">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const isActive = i === step;
            const isDone = i < step;
            return (
              <button
                key={i}
                onClick={() => i <= step && setStep(i)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-2xl text-xs font-semibold transition-all whitespace-nowrap ${
                  isActive ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30" :
                  isDone ? "bg-emerald-50 text-emerald-600 border border-emerald-200" :
                  "bg-white text-gray-400 border border-gray-200"
                }`}
              >
                {isDone ? <Check className="w-3.5 h-3.5" /> : <Icon className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* Form content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* STEP 0 — Location */}
            {step === 0 && (
              <div className="space-y-5">
                <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-5">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-md">
                      <MapPin className="w-4 h-4 text-white" strokeWidth={2.5} />
                    </div>
                    <span className="font-bold text-gray-800">Location Selection</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label className={labelClass}>State</Label>
                      <Input value="Odisha" disabled className={`${inputClass} opacity-60`} />
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>District</Label>
                      <Select value={formData.district} onValueChange={v => update("district", v)}>
                        <SelectTrigger className={inputClass}><SelectValue placeholder="Select district" /></SelectTrigger>
                        <SelectContent>
                          {["Puri","Khurda","Nayagarh","Cuttack","Ganjam"].map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>Block</Label>
                      <Select value={formData.block} onValueChange={v => update("block", v)}>
                        <SelectTrigger className={inputClass}><SelectValue placeholder="Select block" /></SelectTrigger>
                        <SelectContent>
                          {["Puri Sadar","Nimapara","Delang","Konark","Pipili"].map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>Village / Survey No.</Label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                        <Input placeholder="Search village..." value={formData.village} onChange={e => update("village", e.target.value)} className={`pl-9 ${inputClass}`} />
                      </div>
                    </div>
                  </div>

                  {/* Map placeholder */}
                  <div className="h-48 rounded-2xl overflow-hidden relative bg-gray-100 border border-gray-200">
                    <img src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg" alt="" className="w-full h-full object-cover opacity-40" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <MapPin className="w-8 h-8 text-emerald-500 mx-auto mb-2" strokeWidth={2} />
                        <p className="text-xs text-gray-500 font-medium">
                          {formData.district && formData.block ? `${formData.block}, ${formData.district}` : "Select district and block to load map"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 1 — Farmer */}
            {step === 1 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-5">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center shadow-md">
                    <User className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <span className="font-bold text-gray-800">Farmer Linkage</span>
                </div>
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-2xl border border-blue-100">
                  <CornerDownRight className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span className="text-xs text-blue-600">Link this farm to an existing farmer or create a new record</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label className={labelClass}>Farmer Name</Label>
                    <Input placeholder="Enter full name..." value={formData.farmerName} onChange={e => update("farmerName", e.target.value)} className={inputClass} />
                  </div>
                  <div className="space-y-1.5">
                    <Label className={labelClass}>Farmer ID (if existing)</Label>
                    <Input placeholder="e.g. FR-001" value={formData.farmerId} onChange={e => update("farmerId", e.target.value)} className={inputClass} />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2 — Boundary */}
            {step === 2 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-5">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center shadow-md">
                    <Hexagon className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <span className="font-bold text-gray-800">Farm Boundary</span>
                </div>
                <div className="h-52 rounded-2xl overflow-hidden relative bg-gray-900">
                  <img src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg" alt="" className="w-full h-full object-cover opacity-50" />
                  <div className="absolute top-3 left-3 flex gap-2">
                    <button className="px-3 py-1.5 bg-white/90 backdrop-blur-sm rounded-xl text-[10px] font-bold uppercase tracking-wider text-gray-700 flex items-center gap-1 hover:bg-white transition-colors shadow-sm">
                      <Pencil className="w-3 h-3" />Draw Polygon
                    </button>
                    <button className="px-3 py-1.5 bg-white/90 backdrop-blur-sm rounded-xl text-[10px] font-bold uppercase tracking-wider text-gray-700 hover:bg-white transition-colors shadow-sm">
                      Coordinates
                    </button>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Hexagon className="w-8 h-8 text-violet-300 mx-auto mb-2" strokeWidth={1.5} />
                      <p className="text-xs text-white/70">Click corners to draw farm boundary</p>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label className={labelClass}>Polygon Coordinates (GeoJSON)</Label>
                    <Textarea placeholder='[[85.831, 19.814], [85.833, 19.815], ...]' value={formData.coordinates} onChange={e => update("coordinates", e.target.value)} rows={3} className={`${inputClass} font-mono text-xs`} />
                  </div>
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <Label className={labelClass}>Survey Number</Label>
                      <Input placeholder="e.g. RS-1204/56" value={formData.surveyNumber} onChange={e => update("surveyNumber", e.target.value)} className={inputClass} />
                    </div>
                    <div className="space-y-1.5">
                      <Label className={labelClass}>Estimated Area (ha)</Label>
                      <Input placeholder="0.0" value={formData.area} onChange={e => update("area", e.target.value)} className={inputClass} />
                    </div>
                  </div>
                </div>
                {formData.area && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="p-3 bg-violet-50 rounded-2xl border border-violet-100 flex items-center gap-3">
                    <Hexagon className="w-5 h-5 text-violet-500" strokeWidth={2} />
                    <div>
                      <span className="text-xs font-bold text-violet-700">H3 Grid Preview</span>
                      <p className="text-[10px] text-violet-500 mt-0.5">≈ {Math.ceil(parseFloat(formData.area || 0) * 7.5)} cells at resolution 10</p>
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* STEP 3 — Review */}
            {step === 3 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-5">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-md">
                    <FileText className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <span className="font-bold text-gray-800">Review & Confirm</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "State", value: formData.state },
                    { label: "District", value: formData.district || "—" },
                    { label: "Block", value: formData.block || "—" },
                    { label: "Village", value: formData.village || "—" },
                    { label: "Farmer", value: formData.farmerName || "—" },
                    { label: "Farmer ID", value: formData.farmerId || "New" },
                    { label: "Survey No.", value: formData.surveyNumber || "—" },
                    { label: "Area", value: formData.area ? `${formData.area} ha` : "—" },
                  ].map((item, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="p-3 bg-gray-50 rounded-2xl border border-gray-100"
                    >
                      <span className="text-[9px] font-bold uppercase tracking-widest text-gray-400 block mb-1">{item.label}</span>
                      <span className="text-sm font-bold text-gray-800">{item.value}</span>
                    </motion.div>
                  ))}
                </div>
                <Button onClick={handleRegister} className="w-full h-12 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm shadow-lg shadow-emerald-500/30 hover:-translate-y-0.5 transition-all">
                  <Check className="w-4 h-4 mr-2" />Confirm & Register Farm
                </Button>
              </div>
            )}

            {/* STEP 4 — Success */}
            {step === 4 && registered && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 text-center space-y-5"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring", stiffness: 200, damping: 15 }}
                  className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mx-auto shadow-xl shadow-emerald-500/30"
                >
                  <Check className="w-10 h-10 text-white" strokeWidth={3} />
                </motion.div>
                <div>
                  <h2 className="text-2xl font-black text-gray-900">Farm Registered!</h2>
                  <p className="text-sm text-gray-400 mt-1">Now entering the satellite intelligence pipeline</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-left">
                  {[
                    { label: "Farm ID", value: "MF-0089" },
                    { label: "Status", value: "Pipeline Active" },
                    { label: "Timestamp", value: new Date().toISOString().slice(0, 16).replace("T", " ") },
                    { label: "H3 Cells", value: "18 generated" },
                  ].map((item, i) => (
                    <div key={i} className="p-3 bg-emerald-50 rounded-2xl border border-emerald-100">
                      <span className="text-[9px] font-bold uppercase tracking-widest text-emerald-400 block mb-0.5">{item.label}</span>
                      <span className="text-sm font-bold text-gray-800">{item.value}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-3">
                  <Link to="/land-intelligence/MF-0089" className="flex-1">
                    <Button className="w-full h-11 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm shadow-lg shadow-emerald-500/30">
                      View Intelligence <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                  <Button variant="outline" onClick={() => { setStep(0); setRegistered(false); setFormData({ state: "Odisha", district: "", block: "", village: "", surveyNumber: "", farmerId: "", farmerName: "", coordinates: "", area: "" }); }} className="flex-1 h-11 rounded-2xl border-gray-200 text-sm font-semibold">
                    Register Another
                  </Button>
                </div>
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Nav buttons */}
        {step < 4 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center justify-between mt-6"
          >
            <Button
              variant="ghost"
              onClick={() => setStep(s => Math.max(0, s - 1))}
              disabled={step === 0}
              className="h-10 px-5 rounded-2xl text-gray-500 hover:text-gray-800 font-semibold text-sm"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />Back
            </Button>
            {step < 3 && (
              <Button
                onClick={() => setStep(s => Math.min(4, s + 1))}
                disabled={!canNext()}
                className="h-10 px-6 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm shadow-md shadow-emerald-500/20 disabled:opacity-40 transition-all hover:-translate-y-0.5"
              >
                Continue <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}