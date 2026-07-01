import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users, MapPin, Phone, MessageSquare, ChevronRight,
  Search, TrendingUp, Leaf, Hexagon, Building2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import { getFpoFarmers, getFpoFarms, getMyFpo } from "@/lib/api/fpo";

export default function MyFpo() {
  const [view, setView] = useState("map");
  const [search, setSearch] = useState("");
  const [selectedDot, setSelectedDot] = useState(null);
  const [contactFarmer, setContactFarmer] = useState(null);
  const [fpo, setFpo] = useState(null);
  const [farmers, setFarmers] = useState([]);
  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadFpo() {
      setLoading(true);
      setError("");
      try {
        const myFpo = await getMyFpo();
        const [farmersPayload, farmsPayload] = await Promise.all([
          getFpoFarmers(myFpo.fpo_id).catch(() => []),
          getFpoFarms(myFpo.fpo_id).catch(() => []),
        ]);
        if (cancelled) return;
        setFpo(myFpo);
        setFarmers(farmersPayload || []);
        setFarms(farmsPayload || []);
      } catch (err) {
        if (cancelled) return;
        setError(typeof err?.message === "string" ? err.message : "Unable to load FPO farmers.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadFpo();
    return () => {
      cancelled = true;
    };
  }, []);

  const farmerRows = useMemo(() => (
    farmers.map((farmer) => {
      const farmerFarms = farms.filter((farm) => farm.farmer_id === farmer.farmer_id);
      return {
        id: farmer.farmer_id,
        name: farmer.full_name || "Unnamed farmer",
        village: farmer.village_name || "Village unavailable",
        block: farmer.block_name || "Block unavailable",
        farms: farmerFarms.length,
        hectares: farmerFarms.reduce((sum, farm) => sum + Number(farm.area_acres || 0), 0),
        phone: farmer.phone_number || "Not available",
        status: farmer.is_active ? "active" : "pending",
      };
    })
  ), [farmers, farms]);

  const groupedDots = useMemo(() => {
    const blockOrder = [];
    const grouped = new Map();
    farmerRows.forEach((row, index) => {
      const key = row.block || "Unmapped";
      if (!grouped.has(key)) {
        grouped.set(key, { label: key, farmers: [] });
        blockOrder.push(key);
      }
      grouped.get(key).farmers.push(index);
    });

    const positions = [
      { x: "28%", y: "42%" },
      { x: "48%", y: "30%" },
      { x: "18%", y: "58%" },
      { x: "58%", y: "52%" },
      { x: "68%", y: "38%" },
      { x: "15%", y: "45%" },
      { x: "42%", y: "55%" },
      { x: "62%", y: "66%" },
    ];

    return blockOrder.map((key, index) => ({
      ...positions[index % positions.length],
      ...grouped.get(key),
    }));
  }, [farmerRows]);

  const totalHa = useMemo(
    () => farmerRows.reduce((sum, farmer) => sum + Number(farmer.hectares || 0), 0),
    [farmerRows],
  );
  const activeFarmers = useMemo(
    () => farmerRows.filter((farmer) => farmer.status === "active").length,
    [farmerRows],
  );
  const filtered = useMemo(
    () => farmerRows.filter((farmer) =>
      `${farmer.name} ${farmer.village}`.toLowerCase().includes(search.toLowerCase()),
    ),
    [farmerRows, search],
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-slate-100 p-4 md:p-6" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <div className="mx-auto max-w-[1400px] space-y-5">
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/25">
              <Building2 className="h-5 w-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-500">Organisation</span>
              <h1 className="text-xl font-black text-gray-900">My FPO - Farmer Map</h1>
              <p className="text-xs text-gray-500">{fpo?.fpo_name || "Loading FPO..."}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center rounded-2xl border border-gray-200 bg-white p-1 shadow-sm">
              {[{ id: "map", icon: MapPin, label: "Map" }, { id: "list", icon: Users, label: "List" }].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setView(item.id)}
                  className={`flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${view === item.id ? "bg-blue-500 text-white shadow-sm" : "text-gray-500 hover:text-gray-800"}`}
                >
                  <item.icon className="h-3.5 w-3.5" />
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {loading && (
          <div className="rounded-3xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">
            Loading farmer map...
          </div>
        )}

        {!loading && error && (
          <div className="rounded-3xl border border-rose-100 bg-rose-50 p-6 text-sm text-rose-600 shadow-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Total Farmers", value: farmerRows.length, icon: Users, color: "from-blue-400 to-indigo-500" },
            { label: "Active", value: activeFarmers, icon: TrendingUp, color: "from-emerald-400 to-teal-500" },
            { label: "Total Area", value: `${totalHa.toFixed(1)} ac`, icon: Leaf, color: "from-green-400 to-emerald-500" },
            { label: "Total Farms", value: farms.length, icon: Hexagon, color: "from-violet-400 to-purple-500" },
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                className="flex items-center gap-3 rounded-3xl border border-gray-100 bg-white p-4 shadow-sm"
              >
                <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${stat.color} shadow-md`}>
                  <Icon className="h-4.5 w-4.5 text-white" strokeWidth={2.5} />
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
            <motion.div key="map" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <div className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm lg:col-span-2">
                <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
                  <span className="font-bold text-gray-800">Farmer Distribution - Odisha</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{fpo?.district_name || "District"} Cluster</span>
                </div>
                <div className="relative h-[480px] overflow-hidden bg-gray-100">
                  <img
                    src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg"
                    alt="Map"
                    className="h-full w-full object-cover opacity-30"
                  />
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-50/40 to-emerald-50/40" />
                  {groupedDots.map((dot, index) => (
                    <motion.div
                      key={`${dot.label}-${index}`}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: index * 0.1, type: "spring", stiffness: 200, damping: 15 }}
                      className="absolute cursor-pointer"
                      style={{ left: dot.x, top: dot.y, transform: "translate(-50%, -50%)" }}
                      onClick={() => setSelectedDot(selectedDot === index ? null : index)}
                    >
                      <motion.div
                        whileHover={{ scale: 1.15 }}
                        animate={{ boxShadow: selectedDot === index ? "0 0 0 6px rgba(59,130,246,0.2)" : "0 0 0 0 rgba(59,130,246,0)" }}
                        className={`flex items-center justify-center rounded-full transition-all ${
                          dot.farmers.length >= 3 ? "h-12 w-12 bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/40" :
                          dot.farmers.length >= 2 ? "h-9 w-9 bg-gradient-to-br from-emerald-400 to-teal-500 shadow-md shadow-emerald-500/30" :
                          "h-7 w-7 bg-gradient-to-br from-amber-400 to-orange-500 shadow-md shadow-amber-500/30"
                        }`}
                      >
                        <span className="text-xs font-black text-white">{dot.farmers.length}</span>
                      </motion.div>
                      <div className="absolute left-1/2 top-full mt-1.5 -translate-x-1/2 whitespace-nowrap">
                        <span className="rounded-lg bg-white/80 px-2 py-0.5 text-[9px] font-bold text-gray-600 shadow-sm backdrop-blur-sm">{dot.label}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <AnimatePresence mode="wait">
                  {selectedDot !== null && groupedDots[selectedDot] ? (
                    <motion.div key="detail" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm">
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-5 py-4">
                        <span className="font-bold text-gray-800">{groupedDots[selectedDot].label}</span>
                        <p className="mt-0.5 text-[10px] font-semibold text-blue-500">{groupedDots[selectedDot].farmers.length} farmer(s) registered</p>
                      </div>
                      <div className="space-y-2 p-3">
                        {groupedDots[selectedDot].farmers.map((rowIndex) => {
                          const farmer = farmerRows[rowIndex];
                          return (
                            <motion.div key={farmer.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-2xl border border-gray-100 bg-gray-50 p-3 transition-colors hover:border-blue-200">
                              <div className="mb-1 flex items-center justify-between">
                                <Link to={`/farmers/${farmer.id}`} className="text-sm font-bold text-gray-800 transition-colors hover:text-blue-500">{farmer.name}</Link>
                                <VerificationStamp label={farmer.status.toUpperCase()} type={farmer.status === "active" ? "success" : "pending"} compact />
                              </div>
                              <p className="text-[10px] font-medium text-gray-400">{farmer.village} - {farmer.farms} farms - {farmer.hectares.toFixed(1)} ac</p>
                              <div className="mt-2 flex items-center gap-2">
                                <button onClick={() => setContactFarmer(farmer)} className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-blue-500 transition-colors hover:text-blue-700">
                                  <Phone className="h-3 w-3" />
                                  Contact
                                </button>
                                <Link to={`/farmers/${farmer.id}`} className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-emerald-500 transition-colors hover:text-emerald-700">
                                  <ChevronRight className="h-3 w-3" />
                                  Profile
                                </Link>
                              </div>
                            </motion.div>
                          );
                        })}
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="rounded-3xl border border-gray-100 bg-white p-8 text-center shadow-sm">
                      <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
                        <MapPin className="h-7 w-7 text-gray-300" strokeWidth={1.5} />
                      </div>
                      <p className="text-sm font-semibold text-gray-400">Click a dot on the map to view farmers in that area</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence>
                  {contactFarmer && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className="rounded-3xl border border-blue-200 bg-white p-5 shadow-sm">
                      <div className="mb-3 flex items-center justify-between">
                        <span className="text-sm font-bold text-gray-800">Contact - {contactFarmer.name}</span>
                        <button onClick={() => setContactFarmer(null)} className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-xs text-gray-400 transition-colors hover:bg-gray-200">x</button>
                      </div>
                      <div className="mb-4 space-y-2 text-xs text-gray-500">
                        <div className="flex items-center gap-2"><Phone className="h-3.5 w-3.5 text-blue-400" />{contactFarmer.phone}</div>
                        <div className="flex items-center gap-2"><MapPin className="h-3.5 w-3.5 text-rose-400" />{contactFarmer.village}, {contactFarmer.block}</div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" className="h-9 flex-1 rounded-2xl bg-blue-500 text-xs font-semibold text-white shadow-md shadow-blue-500/20 hover:bg-blue-600">
                          <Phone className="mr-1 h-3.5 w-3.5" />
                          Call
                        </Button>
                        <Button size="sm" variant="outline" className="h-9 flex-1 rounded-2xl border-gray-200 text-xs font-semibold">
                          <MessageSquare className="mr-1 h-3.5 w-3.5" />
                          SMS
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ) : (
            <motion.div key="list" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
              <div className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
                  <span className="font-bold text-gray-800">All Farmers</span>
                  <div className="relative w-52">
                    <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
                    <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="h-9 rounded-2xl border-gray-200 bg-gray-50 pl-9 text-xs focus:bg-white" />
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50">
                        {["ID", "Name", "Village", "Block", "Farms", "Area", "Phone", "Status", ""].map((header) => (
                          <th key={header} className="px-4 py-3 text-left text-[9px] font-bold uppercase tracking-widest text-gray-400">{header}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((farmer, index) => (
                        <motion.tr
                          key={farmer.id}
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.04 }}
                          className="border-b border-gray-50 transition-colors hover:bg-blue-50/30 last:border-0"
                        >
                          <td className="px-4 py-3 text-[10px] font-bold text-gray-500">{farmer.id}</td>
                          <td className="px-4 py-3"><Link to={`/farmers/${farmer.id}`} className="font-semibold text-gray-800 transition-colors hover:text-blue-500">{farmer.name}</Link></td>
                          <td className="px-4 py-3 text-gray-400">{farmer.village}</td>
                          <td className="px-4 py-3 text-gray-400">{farmer.block}</td>
                          <td className="px-4 py-3 font-bold text-gray-700">{farmer.farms}</td>
                          <td className="px-4 py-3 font-bold text-gray-700">{farmer.hectares.toFixed(1)}</td>
                          <td className="px-4 py-3 text-gray-400">{farmer.phone}</td>
                          <td className="px-4 py-3"><VerificationStamp label={farmer.status.toUpperCase()} type={farmer.status === "active" ? "success" : "pending"} compact /></td>
                          <td className="px-4 py-3">
                            <Link to={`/farmers/${farmer.id}`} className="flex items-center gap-0.5 text-[10px] font-semibold text-blue-500 transition-colors hover:text-blue-700">
                              View
                              <ChevronRight className="h-3 w-3" />
                            </Link>
                          </td>
                        </motion.tr>
                      ))}
                      {!loading && !error && filtered.length === 0 && (
                        <tr>
                          <td colSpan="9" className="px-4 py-6 text-center text-sm text-gray-500">
                            No farmers found for this FPO.
                          </td>
                        </tr>
                      )}
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
