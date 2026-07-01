import React, { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useInView, useScroll, useTransform } from "framer-motion";
import { ChevronDown, Satellite, Map, BarChart3, Shield, Users, Leaf, ArrowRight, Globe, Database, Layers } from "lucide-react";
import PublicNav from "@/components/layout/PublicNav";

// ─── Pipeline stages with real content ───────────────────────────────────────
const STAGES = [
  {
    num: 1, title: "Field Survey & Registration",
    desc: "Ground-level data capture — farmers register their land parcels with Aadhaar-linked identity, GPS coordinates, and survey numbers via mobile-first forms.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg",
    tag: "Data Capture", color: "from-emerald-400 to-teal-500"
  },
  {
    num: 2, title: "Satellite Scene Acquisition",
    desc: "Sentinel-2 multispectral imagery is pulled over registered farm boundaries on every cloud-free overpass — typically every 5–10 days across India.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/36_vcukad.jpg",
    tag: "Remote Sensing", color: "from-blue-400 to-indigo-500"
  },
  {
    num: 3, title: "H3 Hexagonal Grid Overlay",
    desc: "Farm polygons are tessellated into Uber's H3 hexagonal grid (resolution 10–12), enabling standardized, sub-parcel spatial analysis at scale.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg",
    tag: "Geospatial", color: "from-violet-400 to-purple-500"
  },
  {
    num: 4, title: "NDVI & Vegetation Analysis",
    desc: "Normalized Difference Vegetation Index is computed per H3 cell, tracking crop biomass, phenology, and stress across the season.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg",
    tag: "Spectral Index", color: "from-green-400 to-emerald-600"
  },
  {
    num: 5, title: "Soil Moisture Mapping",
    desc: "Synthetic Aperture Radar (SAR) from Sentinel-1 combined with thermal bands enables soil moisture estimation without ground sensors.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/32_nvof1e.jpg",
    tag: "SAR Analysis", color: "from-cyan-400 to-blue-500"
  },
  {
    num: 6, title: "Cloud Validation & QA",
    desc: "Automated cloud and shadow masking ensures every scene delivered to the platform is high-quality. Scenes below 80% usability are flagged and rejected.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/35_nxcqrp.jpg",
    tag: "Quality Control", color: "from-amber-400 to-orange-500"
  },
  {
    num: 7, title: "FPO Intelligence Dashboard",
    desc: "Block and district-level aggregates give Farmer Producer Organisations a bird's eye view of their entire member portfolio — crop health, area, and alerts.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/34_sgalr8.jpg",
    tag: "Analytics", color: "from-rose-400 to-pink-500"
  },
  {
    num: 8, title: "Verified Land Intelligence Reports",
    desc: "Cryptographically verifiable farm health certificates, usable for crop insurance, institutional credit, and government subsidy verification.",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/37_e3xyru.jpg",
    tag: "Verification", color: "from-teal-400 to-emerald-500"
  },
];

const FEATURE_IMAGES = [
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782727515/23_jbyjb5.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782727514/18_sxrohx.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782727506/24_eg7tee.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782727505/13_i7a9va.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782727503/17_ouwvk8.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726991/9_xsmnqh.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726990/11_f47evp.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726990/5_jlgsrn.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726986/6_ggp6ri.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726988/8_koqpqb.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726987/10_lkw31h.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726984/7_wwkcii.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726978/14_j4c2tl.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726976/21_n8ujvh.jpg",
  "https://res.cloudinary.com/dkst917dg/image/upload/v1782726975/13_vqgl3m.jpg",
];

const STATS = [
  { value: "2.4M+", label: "Hectares Tracked", icon: Globe, color: "text-emerald-500 bg-emerald-50" },
  { value: "140K+", label: "Farmers Registered", icon: Users, color: "text-blue-500 bg-blue-50" },
  { value: "5-day", label: "Satellite Revisit", icon: Satellite, color: "text-violet-500 bg-violet-50" },
  { value: "99.2%", label: "Verification Accuracy", icon: Shield, color: "text-amber-500 bg-amber-50" },
];

const FEATURES = [
  { icon: Satellite, title: "Sentinel-2 Imagery", desc: "10m resolution multispectral data, auto-fetched for every registered farm.", color: "bg-blue-50 text-blue-500" },
  { icon: Map, title: "H3 Geospatial Grid", desc: "Sub-parcel analysis with Uber H3 hexagonal tessellation.", color: "bg-violet-50 text-violet-500" },
  { icon: Leaf, title: "NDVI & Moisture", desc: "Real-time vegetation and soil moisture indices per cell.", color: "bg-emerald-50 text-emerald-500" },
  { icon: BarChart3, title: "FPO Analytics", desc: "Block-level dashboards for Farmer Producer Organisations.", color: "bg-amber-50 text-amber-500" },
  { icon: Shield, title: "Verified Certificates", desc: "Tamper-proof farm health reports for credit and insurance.", color: "bg-rose-50 text-rose-500" },
  { icon: Database, title: "Bulk Data Pipeline", desc: "CSV import, batch raster processing, and audit logs.", color: "bg-teal-50 text-teal-500" },
];

// ─── Stage Card (one-sided: 25% left text / 75% right image) ─────────────────
function StageCard({ stage, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col md:flex-row items-stretch gap-0 rounded-3xl overflow-hidden border border-gray-100 shadow-md bg-white"
    >
      {/* Left — 25% — text & meta */}
      <div className="w-full md:w-1/4 flex flex-col justify-center p-6 md:p-8 bg-white border-b md:border-b-0 md:border-r border-gray-100">
        <div className={`w-10 h-10 rounded-2xl bg-gradient-to-br ${stage.color} flex items-center justify-center shadow-md mb-4`}>
          <span className="text-white font-bold text-sm">{stage.num}</span>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-black mb-2">{stage.tag}</span>
        <h3 className="text-base font-bold text-gray-900 leading-snug mb-3" style={{ fontFamily: "'Poppins', sans-serif" }}>{stage.title}</h3>
        <p className="text-xs text-gray-400 leading-relaxed">{stage.desc}</p>
        <div className={`w-8 h-0.5 rounded-full bg-gradient-to-r ${stage.color} mt-4`} />
      </div>

      {/* Right — 75% — image */}
      <motion.div
        whileHover={{ scale: 1.015 }}
        transition={{ duration: 0.4 }}
        className="w-full md:w-3/4 relative overflow-hidden min-h-[220px] md:min-h-0"
      >
        <img
          src={stage.img}
          alt={stage.title}
          className="w-full h-full object-cover"
          style={{ minHeight: "220px" }}
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-l from-transparent to-black/5" />
      </motion.div>
    </motion.div>
  );
}

// ─── Feature card ─────────────────────────────────────────────────────────────
function FeatureCard({ feature, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });
  const Icon = feature.icon;
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      whileHover={{ y: -4, boxShadow: "0 20px 50px rgba(0,0,0,0.08)" }}
      className="bg-white border border-gray-100 rounded-3xl p-6 space-y-3 cursor-default transition-shadow"
    >
      <div className={`w-11 h-11 rounded-2xl flex items-center justify-center ${feature.color}`}>
        <Icon className="w-5 h-5 strokeWidth={2.5}" />
      </div>
      <h4 className="font-bold text-gray-800 text-sm">{feature.title}</h4>
      <p className="text-xs text-gray-400 leading-relaxed">{feature.desc}</p>
    </motion.div>
  );
}

// ─── Gallery image ────────────────────────────────────────────────────────────
function GalleryImg({ src, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={isInView ? { opacity: 1, scale: 1 } : {}}
      transition={{ duration: 0.5, delay: (index % 5) * 0.07 }}
      whileHover={{ scale: 1.06, zIndex: 10 }}
      className="aspect-square overflow-hidden rounded-2xl cursor-pointer relative"
      style={{ position: "relative" }}
    >
      <img src={src} alt="" className="w-full h-full object-cover" loading="lazy" />
      <div className="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors rounded-2xl" />
    </motion.div>
  );
}

// ─── Home Page ────────────────────────────────────────────────────────────────
export default function Home() {
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <PublicNav />

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section ref={heroRef} className="relative h-screen overflow-hidden">
        <motion.div style={{ y: heroY }} className="absolute inset-0">
          <video autoPlay muted loop playsInline className="w-full h-full object-cover"
            src="https://res.cloudinary.com/dkst917dg/video/upload/v1780464774/vesting_3_rhwasz.mp4" />
          <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/20 to-black/70" />
        </motion.div>

        {/* Hero text overlay */}
        <motion.div
          style={{ opacity: heroOpacity }}
          className="relative z-10 flex flex-col items-center justify-center h-full text-center px-6"
        >
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="space-y-5 max-w-3xl"
          >
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="inline-block text-[10px] uppercase tracking-[0.4em] text-white/60 border border-white/20 rounded-full px-4 py-1.5 backdrop-blur-sm bg-white/5"
            >
              Satellite-Backed Field Intelligence
            </motion.span>
            <h1 className="text-5xl md:text-7xl font-black text-white leading-none tracking-tight"
              style={{ fontFamily: "'Poppins', sans-serif", textShadow: "0 2px 40px rgba(0,0,0,0.4)" }}>
              MaatiTrace
            </h1>
            <p className="text-base md:text-lg text-white/70 max-w-xl mx-auto leading-relaxed font-light">
              From soil to satellite — verifiable land intelligence for India's agricultural ecosystem.
            </p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="flex items-center justify-center gap-4 pt-2"
            >
              <Link to="/register"
                className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-semibold rounded-2xl transition-all shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:-translate-y-0.5">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/our-method"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-2xl backdrop-blur-sm border border-white/20 transition-all">
                Our Method
              </Link>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Scroll cue */}
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-1"
        >
          <span className="text-[9px] uppercase tracking-[0.3em] text-white/40">Scroll</span>
          <ChevronDown className="w-4 h-4 text-white/40" />
        </motion.div>
      </section>

      {/* ── STATS STRIP ──────────────────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="text-center space-y-2"
              >
                <div className={`w-12 h-12 rounded-2xl mx-auto flex items-center justify-center ${s.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <p className="text-3xl font-black text-gray-900">{s.value}</p>
                <p className="text-xs text-gray-400 font-medium">{s.label}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ── WHAT WE DO ───────────────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-4xl mx-auto text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <span className="text-[10px] uppercase tracking-[0.35em] text-gray-400">What We Do</span>
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mt-3 leading-tight" style={{ fontFamily: "'Poppins', sans-serif" }}>
              Land Intelligence,<br />
              <span className="bg-gradient-to-r from-emerald-500 to-teal-500 bg-clip-text text-transparent">Built from the Ground Up</span>
            </h2>
            <p className="text-sm text-gray-400 mt-5 max-w-2xl mx-auto leading-relaxed">
              MaatiTrace connects ground-level field surveys with satellite remote sensing to produce verified, tamper-proof farm intelligence — enabling farmers, FPOs, banks, and insurers to act on real data.
            </p>
          </motion.div>
        </div>
        <div className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => <FeatureCard key={i} feature={f} index={i} />)}
        </div>
      </section>

      {/* ── PIPELINE TIMELINE ────────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-gradient-to-b from-gray-50/80 to-white">
        <div className="max-w-5xl mx-auto">
          <div className="mb-20 text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
              <span className="text-[10px] uppercase tracking-[0.35em] text-gray-400">From Field to Intelligence</span>
              <h2 className="text-4xl md:text-5xl font-black text-gray-900 mt-3" style={{ fontFamily: "'Poppins', sans-serif" }}>
                The MaatiTrace Pipeline
              </h2>
              <p className="text-sm text-gray-400 mt-4 max-w-xl mx-auto">Eight stages from ground survey to verified, satellite-backed intelligence.</p>
            </motion.div>
          </div>
          <div className="space-y-20">
            {STAGES.map((stage, i) => <StageCard key={stage.num} stage={stage} index={i} />)}
          </div>
        </div>
      </section>

      {/* ── GALLERY ──────────────────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="mb-14 text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
              <span className="text-[10px] uppercase tracking-[0.35em] text-gray-400">Ground Coverage</span>
              <h2 className="text-4xl font-black text-gray-900 mt-3" style={{ fontFamily: "'Poppins', sans-serif" }}>In the Field</h2>
            </motion.div>
          </div>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
            {FEATURE_IMAGES.map((src, i) => <GalleryImg key={i} src={src} index={i} />)}
          </div>
        </div>
      </section>

      {/* ── CTA BAND ─────────────────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-gradient-to-br from-emerald-600 via-teal-600 to-emerald-700 relative overflow-hidden">
        {/* Texture dots */}
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "28px 28px" }} />
        <div className="max-w-3xl mx-auto text-center relative">
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="space-y-6">
            <h2 className="text-4xl md:text-5xl font-black text-white" style={{ fontFamily: "'Poppins', sans-serif" }}>
              Ready to map your fields?
            </h2>
            <p className="text-emerald-100 text-sm leading-relaxed max-w-xl mx-auto">
              Join thousands of FPOs and farmers already using satellite intelligence to secure credit, monitor crop health, and prove land ownership.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link to="/register"
                className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-emerald-700 font-bold rounded-2xl text-sm hover:bg-emerald-50 transition-all shadow-xl hover:-translate-y-0.5">
                Register Your FPO <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/login"
                className="inline-flex items-center gap-2 px-6 py-3.5 border border-white/30 text-white font-medium rounded-2xl text-sm hover:bg-white/10 transition-all">
                Sign In
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 py-10 px-6 bg-white">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-emerald-500 flex items-center justify-center">
              <Layers className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-black text-sm text-gray-900">MAATITRACE</span>
              <span className="text-[9px] text-gray-400 uppercase tracking-wider ml-2 hidden sm:inline">Field Intelligence Platform</span>
            </div>
          </div>
          <div className="flex items-center gap-5 text-[11px] text-gray-400">
            <Link to="/use-cases" className="hover:text-gray-900 transition-colors">Use Cases</Link>
            <Link to="/our-method" className="hover:text-gray-900 transition-colors">Methodology</Link>
            <Link to="/login" className="hover:text-gray-900 transition-colors">Sign In</Link>
          </div>
          <p className="text-[10px] text-gray-300 w-full md:w-auto text-center md:text-right">© 2026 MaatiTrace. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}