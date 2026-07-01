import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Users, MapPin, Phone, MessageSquare, ChevronRight,
  Search, TrendingUp, Leaf, Hexagon, Building2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import { motion, AnimatePresence } from "framer-motion";

const DEMO_FARMERS = [
  { id: "FR-001", name: "Ramesh Sahoo", village: "Baliguali", block: "Puri Sadar", farms: 3, hectares: 7.2, phone: "+91 98765 43210", status: "active" },
  { id: "FR-002", name: "Sita Behera", village: "Chandanpur", block: "Nayagarh", farms: 2, hectares: 4.8, phone: "+91 98765 43211", status: "active" },
  { id: "FR-003", name: "Mohan Pradhan", village: "Konark", block: "Puri Sadar", farms: 1, hectares: 2.1, phone: "+91 98765 43212", status: "pending" },
  { id: "FR-004", name: "Lakshmi Das", village: "Pipili", block: "Delang", farms: 4, hectares: 9.6, phone: "+91 98765 43213", status: "active" },
  { id: "FR-005", name: "Bijay Naik", village: "Nimapara", block: "Nimapara", farms: 2, hectares: 5.3, phone: "+91 98765 43214", status: "active" },
  { id: "FR-006", name: "Gopal Mishra", village: "Astaranga", block: "Puri Sadar", farms: 2, hectares: 3.8, phone: "+91 98765 43215", status: "active" },
  { id: "FR-007", name: "Priya Swain", village: "Brahmagiri", block: "Brahmagiri", farms: 3, hectares: 6.5, phone: "+91 98765 43216", status: "active" },
  { id: "FR-008", name: "Durga Jena", village: "Satyabadi", block: "Satyabadi", farms: 1, hectares: 1.9, phone: "+91 98765 43217", status: "pending" },
];

const MAP_DOTS = [
  { x: "28%", y: "42%", farmers: [0, 2, 5], label: "Puri Sadar" },
  { x: "48%", y: "30%", farmers: [4], label: "Nimapara" },
  { x: "18%", y: "58%", farmers: [1], label: "Nayagarh" },
  { x: "58%", y: "52%", farmers: [3], label: "Delang" },
  { x: "68%", y: "38%", farmers: [5], label: "Astaranga" },
  { x: "15%", y: "45%", farmers: [6], label: "Brahmagiri" },
  { x: "42%", y: "55%", farmers: [7], label: "Satyabadi" },
];

const totalHa = DEMO_FARMERS.reduce((s, f) => s + f.hectares, 0);
const activeFarmers = DEMO_FARMERS.filter(f => f.status === "active").length;

export default function MyFpo() {
  const [view, setView] = useState("map");
  const [search, setSearch] = useState("");
  const [selectedDot, setSelectedDot] = useState(null);
  const [contactFarmer, setContactFarmer] = useState(null);

  const filtered = DEMO_FARMERS.filter(f =>
    f.name.toLowerCase().includes(search.toLowerCase()) ||
    f.village.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-slate-100 p-4 md:p-6" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <div className="max-w-[1400px] mx-auto space-y-5">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <Building2 className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-500">Organisation</span>
              <h1 className="text-xl font-black text-gray-900">My FPO — Farmer Map</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-white rounded-2xl border border-gray-200 p-1 shadow-sm">
              {[{ id: "map", icon: MapPin, label: "Map" }, { id: "list", icon: Users, label: "List" }].map(v => (
                <button
                  key={v.id}
                  onClick={() => setView(v.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${view === v.id ? "bg-blue-500 text-white shadow-sm" : "text-gray-500 hover:text-gray-800"}`}
                >
                  <v.icon className="w-3.5 h-3.5" />{v.label}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Stats strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Farmers", value: DEMO_FARMERS.length, icon: Users, color: "from-blue-400 to-indigo-500" },
            { label: "Active", value: activeFarmers, icon: TrendingUp, color: "from-emerald-400 to-teal-500" },
            { label: "Total Area", value: `${totalHa.toFixed(1)} ha`, icon: Leaf, color: "from-green-400 to-emerald-500" },
            { label: "Total Farms", value: DEMO_FARMERS.reduce((s,f)=>s+f.farms,0), icon: Hexagon, color: "from-violet-400 to-purple-500" },
          ].map((stat, i) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="bg-white rounded-3xl p-4 shadow-sm border border-gray-100 flex items-center gap-3"
              >
                <div className={`w-10 h-10 rounded-2xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-md flex-shrink-0`}>
                  <Icon className="w-4.5 h-4.5 text-white" strokeWidth={2.5} />
                </div>
                <div>
                  <p className="text-lg font-black text-gray-900">{stat.value}</p>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{stat.label}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        <AnimatePresence mode="wait">
          {view === "map" ? (
            <motion.div key="map" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Map */}
              <div className="lg:col-span-2 bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <span className="font-bold text-gray-800">Farmer Distribution — Odisha</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Puri District Cluster</span>
                </div>
                <div className="h-[480px] relative overflow-hidden bg-gray-100">
                  <img
                    src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg"
                    alt="Map"
                    className="w-full h-full object-cover opacity-30"
                  />
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-50/40 to-emerald-50/40" />
                  {MAP_DOTS.map((dot, i) => (
                    <motion.div
                      key={i}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.1, type: "spring", stiffness: 200, damping: 15 }}
                      className="absolute cursor-pointer"
                      style={{ left: dot.x, top: dot.y, transform: "translate(-50%, -50%)" }}
                      onClick={() => setSelectedDot(selectedDot === i ? null : i)}
                    >
                      <motion.div
                        whileHover={{ scale: 1.15 }}
                        animate={{ boxShadow: selectedDot === i ? "0 0 0 6px rgba(59,130,246,0.2)" : "0 0 0 0px rgba(59,130,246,0)" }}
                        className={`rounded-full flex items-center justify-center transition-all ${
                          dot.farmers.length >= 3 ? "w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/40" :
                          dot.farmers.length >= 2 ? "w-9 h-9 bg-gradient-to-br from-emerald-400 to-teal-500 shadow-md shadow-emerald-500/30" :
                          "w-7 h-7 bg-gradient-to-br from-amber-400 to-orange-500 shadow-md shadow-amber-500/30"
                        }`}
                      >
                        <span className="font-black text-white text-xs">{dot.farmers.length}</span>
                      </motion.div>
                      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1.5 whitespace-nowrap">
                        <span className="text-[9px] font-bold text-gray-600 bg-white/80 backdrop-blur-sm px-2 py-0.5 rounded-lg shadow-sm">{dot.label}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Side panel */}
              <div className="space-y-3">
                <AnimatePresence mode="wait">
                  {selectedDot !== null ? (
                    <motion.div key="detail" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
                      <div className="px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
                        <span className="font-bold text-gray-800">{MAP_DOTS[selectedDot].label}</span>
                        <p className="text-[10px] text-blue-500 font-semibold mt-0.5">{MAP_DOTS[selectedDot].farmers.length} farmer(s) registered</p>
                      </div>
                      <div className="p-3 space-y-2">
                        {MAP_DOTS[selectedDot].farmers.map(fi => {
                          const f = DEMO_FARMERS[fi];
                          return (
                            <motion.div key={f.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 bg-gray-50 rounded-2xl border border-gray-100 hover:border-blue-200 transition-colors">
                              <div className="flex items-center justify-between mb-1">
                                <Link to={`/farmer-profile/${f.id}`} className="text-sm font-bold text-gray-800 hover:text-blue-500 transition-colors">{f.name}</Link>
                                <VerificationStamp label={f.status.toUpperCase()} type={f.status === "active" ? "success" : "pending"} compact />
                              </div>
                              <p className="text-[10px] text-gray-400 font-medium">{f.village} · {f.farms} farms · {f.hectares} ha</p>
                              <div className="flex items-center gap-2 mt-2">
                                <button onClick={() => setContactFarmer(f)} className="text-[9px] font-bold uppercase tracking-wider text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors">
                                  <Phone className="w-3 h-3" />Contact
                                </button>
                                <Link to={`/farmer-profile/${f.id}`} className="text-[9px] font-bold uppercase tracking-wider text-emerald-500 hover:text-emerald-700 flex items-center gap-1 transition-colors">
                                  <ChevronRight className="w-3 h-3" />Profile
                                </Link>
                              </div>
                            </motion.div>
                          );
                        })}
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8 text-center">
                      <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
                        <MapPin className="w-7 h-7 text-gray-300" strokeWidth={1.5} />
                      </div>
                      <p className="text-sm font-semibold text-gray-400">Click a dot on the map to view farmers in that area</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence>
                  {contactFarmer && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className="bg-white rounded-3xl border border-blue-200 shadow-sm p-5">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-bold text-gray-800">Contact — {contactFarmer.name}</span>
                        <button onClick={() => setContactFarmer(null)} className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 hover:bg-gray-200 transition-colors text-xs">✕</button>
                      </div>
                      <div className="space-y-2 text-xs text-gray-500 mb-4">
                        <div className="flex items-center gap-2"><Phone className="w-3.5 h-3.5 text-blue-400" />{contactFarmer.phone}</div>
                        <div className="flex items-center gap-2"><MapPin className="w-3.5 h-3.5 text-rose-400" />{contactFarmer.village}, {contactFarmer.block}</div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" className="flex-1 h-9 rounded-2xl bg-blue-500 hover:bg-blue-600 text-white font-semibold text-xs shadow-md shadow-blue-500/20">
                          <Phone className="w-3.5 h-3.5 mr-1" />Call
                        </Button>
                        <Button size="sm" variant="outline" className="flex-1 h-9 rounded-2xl border-gray-200 font-semibold text-xs">
                          <MessageSquare className="w-3.5 h-3.5 mr-1" />SMS
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ) : (
            <motion.div key="list" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
              <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                  <span className="font-bold text-gray-800">All Farmers</span>
                  <div className="relative w-52">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                    <Input placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} className="pl-9 h-9 text-xs rounded-2xl border-gray-200 bg-gray-50 focus:bg-white" />
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50">
                        {["ID", "Name", "Village", "Block", "Farms", "Hectares", "Phone", "Status", ""].map(h => (
                          <th key={h} className="text-left px-4 py-3 text-[9px] font-bold uppercase tracking-widest text-gray-400">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((f, i) => (
                        <motion.tr
                          key={f.id}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.04 }}
                          className="border-b border-gray-50 last:border-0 hover:bg-blue-50/30 transition-colors"
                        >
                          <td className="px-4 py-3 font-bold text-gray-500 text-[10px]">{f.id}</td>
                          <td className="px-4 py-3"><Link to={`/farmer-profile/${f.id}`} className="font-semibold text-gray-800 hover:text-blue-500 transition-colors">{f.name}</Link></td>
                          <td className="px-4 py-3 text-gray-400">{f.village}</td>
                          <td className="px-4 py-3 text-gray-400">{f.block}</td>
                          <td className="px-4 py-3 font-bold text-gray-700">{f.farms}</td>
                          <td className="px-4 py-3 font-bold text-gray-700">{f.hectares}</td>
                          <td className="px-4 py-3 text-gray-400">{f.phone}</td>
                          <td className="px-4 py-3"><VerificationStamp label={f.status.toUpperCase()} type={f.status === "active" ? "success" : "pending"} compact /></td>
                          <td className="px-4 py-3">
                            <Link to={`/farmer-profile/${f.id}`} className="flex items-center gap-0.5 text-blue-500 hover:text-blue-700 font-semibold text-[10px] transition-colors">
                              View <ChevronRight className="w-3 h-3" />
                            </Link>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}