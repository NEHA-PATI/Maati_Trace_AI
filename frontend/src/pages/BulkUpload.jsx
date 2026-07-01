import React, { useState } from "react";
import {
  FileUp, Download, Check, X, AlertTriangle,
  ChevronRight, Loader2, Layers, Zap, ShieldCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

const DEMO_VALIDATION = [
  { row: 1, farmer: "Ramesh Sahoo", village: "Baliguali", block: "Puri Sadar", area: "2.4", status: "valid" },
  { row: 2, farmer: "Sita Behera", village: "Chandanpur", block: "Nayagarh", area: "3.1", status: "valid" },
  { row: 3, farmer: "Mohan P.", village: "Konark", block: "Puri Sadar", area: "1.8", status: "valid" },
  { row: 4, farmer: "Bijay Naik", village: "", block: "Nimapara", area: "2.0", status: "error", error: "Village name missing" },
  { row: 5, farmer: "Lakshmi Das", village: "Pipili", block: "Delang", area: "-1.5", status: "error", error: "Invalid area value" },
  { row: 6, farmer: "Gopal Mishra", village: "Astaranga", block: "Puri Sadar", area: "4.2", status: "valid" },
];

const STEPS = ["Upload CSV", "Validate", "Review", "Process", "Report"];

function StepBar({ current }) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {STEPS.map((s, i) => (
        <React.Fragment key={i}>
          <div className="flex flex-col items-center gap-1.5">
            <motion.div
              animate={{
                backgroundColor: i < current ? "#10b981" : i === current ? "#10b981" : "#e5e7eb",
                scale: i === current ? 1.15 : 1,
              }}
              className="w-8 h-8 rounded-full flex items-center justify-center shadow-sm"
            >
              {i < current ? (
                <Check className="w-3.5 h-3.5 text-white" strokeWidth={3} />
              ) : (
                <span className="text-[10px] font-bold text-white" style={{ color: i >= current ? "#9ca3af" : "white" }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
              )}
            </motion.div>
            <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400 hidden sm:block">{s}</span>
          </div>
          {i < STEPS.length - 1 && (
            <motion.div
              animate={{ backgroundColor: i < current ? "#10b981" : "#e5e7eb" }}
              className="flex-1 h-0.5 mx-1"
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

export default function BulkUpload() {
  const [phase, setPhase] = useState("upload");
  const [progress, setProgress] = useState(0);
  const [dragging, setDragging] = useState(false);

  const startValidation = () => {
    setPhase("validating");
    let p = 0;
    const interval = setInterval(() => {
      p += 15;
      if (p >= 100) { clearInterval(interval); setPhase("validated"); setProgress(100); }
      else setProgress(p);
    }, 300);
  };

  const startProcessing = () => {
    setPhase("processing"); setProgress(0);
    let p = 0;
    const interval = setInterval(() => {
      p += 10;
      if (p >= 100) { clearInterval(interval); setPhase("complete"); setProgress(100); }
      else setProgress(p);
    }, 400);
  };

  const phaseIndex = { upload: 0, validating: 1, validated: 2, processing: 3, complete: 4 };
  const validRows = DEMO_VALIDATION.filter(r => r.status === "valid");
  const errorRows = DEMO_VALIDATION.filter(r => r.status === "error");

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-slate-100 p-4 md:p-8" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Layers className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-500">Bulk Pipeline</span>
              <h1 className="text-2xl font-black text-gray-900">Bulk Farm Upload</h1>
            </div>
          </div>
          <p className="text-sm text-gray-400 ml-13">Upload CSV to register multiple farms through the satellite pipeline</p>
        </motion.div>

        <StepBar current={phaseIndex[phase]} />

        <AnimatePresence mode="wait">
          {/* UPLOAD */}
          {phase === "upload" && (
            <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-5 border-b border-gray-100 flex items-center justify-between">
                  <span className="font-bold text-gray-800">Upload Farm Data CSV</span>
                  <Button size="sm" variant="ghost" className="h-8 text-xs rounded-2xl text-gray-500 hover:text-gray-800">
                    <Download className="w-3.5 h-3.5 mr-1.5" />Download Template
                  </Button>
                </div>
                <div className="p-8">
                  <motion.div
                    animate={{ borderColor: dragging ? "#10b981" : "#e5e7eb", backgroundColor: dragging ? "#f0fdf4" : "#fafafa" }}
                    onDragOver={e => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={e => { e.preventDefault(); setDragging(false); startValidation(); }}
                    onClick={startValidation}
                    className="border-2 border-dashed rounded-3xl p-14 text-center cursor-pointer transition-all hover:border-emerald-300 hover:bg-emerald-50/50 group"
                  >
                    <motion.div
                      animate={{ y: dragging ? -4 : 0 }}
                      className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center mx-auto mb-4 group-hover:from-emerald-50 group-hover:to-teal-100 transition-all"
                    >
                      <FileUp className="w-7 h-7 text-blue-400 group-hover:text-emerald-500 transition-colors" strokeWidth={2} />
                    </motion.div>
                    <p className="text-base font-bold text-gray-700 mb-1">Drop CSV file here or click to browse</p>
                    <p className="text-xs text-gray-400">Accepts .csv files · max 500 rows per upload</p>
                    <div className="mt-4 flex flex-wrap justify-center gap-2">
                      {["farmer_name", "village", "block", "district", "coordinates", "survey_number"].map(col => (
                        <span key={col} className="px-2.5 py-1 bg-gray-100 rounded-lg text-[9px] font-bold uppercase tracking-wider text-gray-500">{col}</span>
                      ))}
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          )}

          {/* VALIDATING / PROCESSING */}
          {(phase === "validating" || phase === "processing") && (
            <motion.div key={phase} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-12 text-center space-y-6">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                  className="w-16 h-16 rounded-full border-4 border-gray-100 border-t-emerald-500 mx-auto"
                />
                <div>
                  <p className="text-lg font-bold text-gray-800">
                    {phase === "validating" ? "Validating CSV rows..." : "Processing farm registrations..."}
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    {phase === "validating" ? "Checking locations, farmer data, coordinates" : "Registering farms, generating H3 cells"}
                  </p>
                </div>
                <div className="max-w-xs mx-auto">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full"
                      style={{ width: `${progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <p className="text-sm font-bold text-emerald-500 mt-2">{progress}%</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* VALIDATED */}
          {phase === "validated" && (
            <motion.div key="validated" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: "Total Rows", value: DEMO_VALIDATION.length, color: "from-blue-400 to-indigo-500" },
                  { label: "Valid", value: validRows.length, color: "from-emerald-400 to-teal-500" },
                  { label: "Errors", value: errorRows.length, color: "from-rose-400 to-red-500" },
                ].map((stat, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100 text-center"
                  >
                    <div className={`text-3xl font-black bg-gradient-to-br ${stat.color} bg-clip-text text-transparent`}>{stat.value}</div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mt-1">{stat.label}</p>
                  </motion.div>
                ))}
              </div>

              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100">
                  <span className="font-bold text-gray-800">Validation Results</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50">
                        {["Row", "Farmer", "Village", "Block", "Area", "Status", "Note"].map(h => (
                          <th key={h} className="text-left px-4 py-3 text-[9px] font-bold uppercase tracking-widest text-gray-400">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {DEMO_VALIDATION.map((r, i) => (
                        <motion.tr
                          key={r.row}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className={`border-b border-gray-50 last:border-0 ${r.status === "error" ? "bg-rose-50/50" : ""}`}
                        >
                          <td className="px-4 py-3 font-bold text-gray-700">{String(r.row).padStart(2, "0")}</td>
                          <td className="px-4 py-3 font-medium text-gray-700">{r.farmer}</td>
                          <td className="px-4 py-3 text-gray-500">{r.village || <span className="text-rose-500 font-semibold">Missing</span>}</td>
                          <td className="px-4 py-3 text-gray-500">{r.block}</td>
                          <td className="px-4 py-3 text-gray-500">{r.area}</td>
                          <td className="px-4 py-3">
                            {r.status === "valid"
                              ? <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-lg text-[9px] font-bold"><Check className="w-3 h-3" />Valid</span>
                              : <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-rose-50 text-rose-600 rounded-lg text-[9px] font-bold"><X className="w-3 h-3" />Error</span>
                            }
                          </td>
                          <td className="px-4 py-3 text-rose-500 text-[10px]">{r.error || "—"}</td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setPhase("upload")} className="h-11 px-6 rounded-2xl border-gray-200 font-semibold">
                  Re-upload
                </Button>
                <Button onClick={startProcessing} className="h-11 px-6 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold shadow-lg shadow-emerald-500/20 hover:-translate-y-0.5 transition-all">
                  Process {validRows.length} Valid Rows <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </motion.div>
          )}

          {/* COMPLETE */}
          {phase === "complete" && (
            <motion.div key="complete" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-10 text-center space-y-6">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.1 }}
                  className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mx-auto shadow-xl shadow-emerald-500/30"
                >
                  <ShieldCheck className="w-10 h-10 text-white" strokeWidth={2.5} />
                </motion.div>
                <div>
                  <h2 className="text-2xl font-black text-gray-900">Batch Processing Complete</h2>
                  <p className="text-sm text-gray-400 mt-1">{validRows.length} farms registered · {errorRows.length} rows skipped</p>
                </div>
                <div className="grid grid-cols-2 gap-3 max-w-xs mx-auto text-left">
                  {[
                    { icon: Zap, label: "Farms Created", value: `${validRows.length}` },
                    { icon: AlertTriangle, label: "Skipped Rows", value: `${errorRows.length}` },
                  ].map(({ icon: Icon, label, value }, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-2xl border border-gray-100">
                      <span className="text-[9px] font-bold uppercase tracking-widest text-gray-400 block mb-0.5">{label}</span>
                      <span className="text-lg font-black text-gray-800">{value}</span>
                    </div>
                  ))}
                </div>
                <div className="flex justify-center gap-3">
                  <Button variant="outline" className="h-11 px-6 rounded-2xl border-gray-200 font-semibold">
                    <Download className="w-4 h-4 mr-1.5" />Download Report
                  </Button>
                  <Button onClick={() => { setPhase("upload"); setProgress(0); }} className="h-11 px-6 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold shadow-lg shadow-emerald-500/20 hover:-translate-y-0.5 transition-all">
                    Upload Another Batch
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}