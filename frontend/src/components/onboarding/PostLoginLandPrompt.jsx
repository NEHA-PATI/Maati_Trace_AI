import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { getMyFarmerProfile, getFarmerFarms } from "@/lib/api/farmer";
import { getMyFpo, getFpoFarmers, getFpoFarms } from "@/lib/api/fpo";

const KEY = "maatitrace_land_prompt_dismissed";
export default function PostLoginLandPrompt({ user }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (sessionStorage.getItem(KEY)) return;
    (async () => {
      try {
        if (user?.role === "farmer") {
          const farmer = await getMyFarmerProfile(); const farms = await getFarmerFarms(farmer.farmer_id).catch(() => []);
          if (!farms.length) setOpen(true);
        } else if (user?.role === "fpo") {
          const fpo = await getMyFpo(); const farmers = await getFpoFarmers(fpo.fpo_id).catch(() => []); const farms = await getFpoFarms(fpo.fpo_id).catch(() => []);
          if (!farmers.length || !farms.length) setOpen(true);
        }
      } catch {}
    })();
  }, [user?.role]);
  const dismiss = () => { sessionStorage.setItem(KEY, "1"); setOpen(false); };
  return <AnimatePresence>{open && <motion.div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    <motion.div initial={{ y: 20, scale: 0.95 }} animate={{ y: 0, scale: 1 }} exit={{ y: 20, scale: 0.95 }} className="w-full max-w-lg rounded-[2rem] border border-white/40 bg-white/85 p-6 shadow-2xl">
      <h3 className="text-2xl font-black">{user?.role === "farmer" ? "Register your first land" : "Start your FPO workspace"}</h3>
      <p className="mt-2 text-sm text-slate-600">{user?.role === "farmer" ? "MaatiTrace needs your farm boundary to start satellite intelligence." : "Add farmers, register land, or upload in bulk to unlock the workspace."}</p>
      <div className="mt-5 flex flex-wrap gap-3">
        {user?.role === "farmer" ? <Link to="/farm-register" className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white">Register Land Now</Link> : <>
          <Link to="/my-fpo" className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white">Add Farmer</Link>
          <Link to="/farm-register" className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold">Register Land</Link>
          <Link to="/bulk-upload" className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold">Bulk Upload</Link>
        </>}
        <button onClick={dismiss} className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold">Later</button>
      </div>
    </motion.div></motion.div>}</AnimatePresence>;
}
