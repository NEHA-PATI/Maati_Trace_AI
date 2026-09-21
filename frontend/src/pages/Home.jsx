import React, { useRef } from "react";
import { Link } from "react-router-dom";
import { motion as Motion, useScroll, useTransform } from "framer-motion";
import {
  ChevronDown, ArrowRight, Layers, Check,
  Tractor, Users, Factory, Waypoints, Globe,
  Satellite, BrainCircuit, Sprout, Sparkles,
  Eye, Gauge, Lightbulb, Zap,
  MapPin, Wheat, BadgeCheck, Store,
  Droplets, Leaf, FileText,
  ShieldCheck, TrendingUp, QrCode,
} from "lucide-react";
import PublicNav from "@/components/layout/PublicNav";

// ── Imagery: hotlinked stock photos (Unsplash) chosen to match the reference ─
const IMG = {
  intelBg: "https://images.unsplash.com/photo-1495107334309-fcf20504a5ab?auto=format&fit=crop&w=1600&q=80",
  satellite: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1000&q=80",
  ml: "https://images.unsplash.com/photo-1555949963-aa79dcee981c?auto=format&fit=crop&w=1000&q=80",
  ground: "https://images.unsplash.com/photo-1500076656116-558758c991c1?auto=format&fit=crop&w=1000&q=80",
  ai: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80",
  solFarmers: "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1200&q=80",
  solFpos: "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1200&q=80",
  solExport: "https://images.unsplash.com/photo-1494412519320-aa613dfb7738?auto=format&fit=crop&w=1200&q=80",
  sustain: "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1400&q=80",
  ctaBg: "https://images.unsplash.com/photo-1500595046743-cd271d694d30?auto=format&fit=crop&w=2000&q=80",
};

const ECOSYSTEM = [
  { icon: Tractor, title: "Farmers", desc: "Manage farms, crops and practices" },
  { icon: Users, title: "FPOs", desc: "Aggregate, manage and grow together" },
  { icon: Factory, title: "Processors", desc: "Ensure quality and process efficiency" },
  { icon: Waypoints, title: "Confederations", desc: "Oversee networks and programmes" },
  { icon: Globe, title: "Exporters & Buyers", desc: "Source with confidence, sell with trust" },
];

const INTEL_SOURCES = [
  { icon: Satellite, title: "Satellite", desc: "Observe change at scale", img: IMG.satellite },
  { icon: BrainCircuit, title: "ML Prediction", desc: "Crop and farm land predictions", img: IMG.ml },
  { icon: Sprout, title: "Ground & Soil", desc: "Measure real conditions", img: IMG.ground },
  { icon: Sparkles, title: "AI Intelligence", desc: "Turn data into actionable insights", img: IMG.ai },
];

const INTEL_FLOW = [
  { icon: Eye, label: "Observe" },
  { icon: Gauge, label: "Measure" },
  { icon: Lightbulb, label: "Understand" },
  { icon: Zap, label: "Act" },
];

const SOLUTIONS = [
  {
    audience: "For Farmers", title: "Know Your Farm.",
    desc: "Make better decisions with a connected digital view of your farm.",
    points: ["Crop & soil insights", "Smart advisories", "Digital farm records", "Sustainability tracking"],
    cta: "Explore for Farmers", to: "/use-cases", img: IMG.solFarmers,
  },
  {
    audience: "For FPOs", title: "Know Your Network.",
    desc: "Bring farmer, production and aggregation data together.",
    points: ["Farmer & crop management", "Aggregation & quality tracking", "Traceable supply chains", "Business intelligence"],
    cta: "Explore for FPOs", to: "/use-cases", img: IMG.solFpos,
  },
  {
    audience: "For Confederations & Exporters", title: "Know Your Value Chain.",
    desc: "Build confidence from origin to buyer with evidence-backed records.",
    points: ["End-to-end traceability", "Compliance & certifications", "Sustainability evidence", "Buyer confidence"],
    cta: "Explore for Exporters", to: "/use-cases", img: IMG.solExport,
  },
];

const JOURNEY = [
  { icon: MapPin, title: "Farm", sub: "Origin" },
  { icon: Sprout, title: "Crop", sub: "Cultivation" },
  { icon: Wheat, title: "Harvest", sub: "Production" },
  { icon: Factory, title: "Processing", sub: "Batch" },
  { icon: BadgeCheck, title: "Quality", sub: "Evidence" },
  { icon: Store, title: "Market", sub: "Confidence" },
];

const TRACE_ITEMS = [
  { icon: MapPin, label: "Farm", desc: "Origin, farmer and location" },
  { icon: Sprout, label: "Crop", desc: "Crop and cultivation information" },
  { icon: Wheat, label: "Harvest", desc: "Harvest event and quantity" },
  { icon: BadgeCheck, label: "Quality", desc: "Quality and batch evidence" },
  { icon: Store, label: "Market", desc: "Traceable product story" },
];

const SUSTAIN = [
  { icon: Sprout, title: "Land & Soil", desc: "Measurable agricultural conditions" },
  { icon: Droplets, title: "Resources", desc: "Visibility of resource management" },
  { icon: Leaf, title: "Impact", desc: "Evidence for sustainability claims" },
  { icon: FileText, title: "Reporting", desc: "Operational data for reporting" },
];

const IMPACT = [
  { icon: Lightbulb, title: "Better Decisions", desc: "Data-driven agricultural insights" },
  { icon: Eye, title: "End-to-End Visibility", desc: "Connected value chains" },
  { icon: ShieldCheck, title: "Trusted Traceability", desc: "Evidence from origin to market" },
  { icon: TrendingUp, title: "Sustainable Growth", desc: "Better outcomes for people and planet" },
];

const EASE = [0.22, 1, 0.36, 1];
const containerV = { hidden: {}, show: { transition: { staggerChildren: 0.09, delayChildren: 0.04 } } };
const itemV = { hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } } };

function Reveal({ children, delay = 0, className = "" }) {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 26 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: EASE }}
      className={className}
    >
      {children}
    </Motion.div>
  );
}

function Stagger({ children, className = "" }) {
  return (
    <Motion.div variants={containerV} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-70px" }} className={className}>
      {children}
    </Motion.div>
  );
}

function Item({ children, className = "" }) {
  return <Motion.div variants={itemV} className={className}>{children}</Motion.div>;
}

function TimelineLine({ className }) {
  return (
    <Motion.div
      aria-hidden
      initial={{ scaleX: 0 }}
      whileInView={{ scaleX: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 1, ease: "easeInOut" }}
      style={{ transformOrigin: "left" }}
      className={className}
    />
  );
}

function SectionHead({ kicker, title, lead, dark = false, center = false }) {
  return (
    <Reveal className={`${center ? "mx-auto text-center" : ""} max-w-3xl`}>
      <span className={`inline-flex items-center gap-3 text-[12px] font-extrabold uppercase tracking-[0.3em] md:text-[13px] ${dark ? "text-[#b9e84d]" : "text-emerald-600"}`}>
        {!center && <span className={`h-[3px] w-8 rounded-full ${dark ? "bg-[#b9e84d]" : "bg-emerald-600"}`} />}
        {kicker}
      </span>
      <h2 className={`mt-4 text-[34px] font-black leading-[0.98] tracking-[-0.02em] sm:text-5xl md:text-6xl ${dark ? "text-white" : "text-gray-900"}`}>
        {title}
      </h2>
      {lead && (
        <p className={`mt-5 text-base leading-relaxed md:text-xl ${dark ? "text-white/70" : "text-gray-500"}`}>
          {lead}
        </p>
      )}
    </Reveal>
  );
}

export default function Home() {
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: "'Poppins', sans-serif" }}>
      <PublicNav />

      {/* ── HERO (unchanged) ─────────────────────────────────────────────── */}
      <section ref={heroRef} className="relative h-screen overflow-hidden">
        <Motion.div style={{ y: heroY }} className="absolute inset-0">
          <video autoPlay muted loop playsInline className="w-full h-full object-cover"
            src="https://res.cloudinary.com/dkst917dg/video/upload/v1782894887/home_page_vdo_1_vcroju.mp4" />
          <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/20 to-black/70" />
        </Motion.div>

        <Motion.div
          style={{ opacity: heroOpacity }}
          className="relative z-10 flex flex-col items-center justify-center h-full text-center px-6"
        >
          <Motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="space-y-5 max-w-3xl"
          >
            <Motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="inline-block text-[10px] uppercase tracking-[0.4em] text-white/60 border border-white/20 rounded-full px-4 py-1.5 backdrop-blur-sm bg-white/5"
            >
              Satellite-Backed Field Intelligence
            </Motion.span>
            <h1 className="text-5xl md:text-7xl font-black text-white leading-none tracking-tight"
              style={{ fontFamily: "'Poppins', sans-serif", textShadow: "0 2px 40px rgba(0,0,0,0.4)" }}>
              MaatiTrace
            </h1>
            <p className="text-base md:text-lg text-white/70 max-w-xl mx-auto leading-relaxed font-light">
              From soil to satellite — verifiable land intelligence for India's agricultural ecosystem.
            </p>
            <Motion.div
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
            </Motion.div>
          </Motion.div>
        </Motion.div>

        <Motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-1"
        >
          <span className="text-[9px] uppercase tracking-[0.3em] text-white/40">Scroll</span>
          <ChevronDown className="w-4 h-4 text-white/40" />
        </Motion.div>
      </section>

      {/* ── ECOSYSTEM ────────────────────────────────────────────────────── */}
      <section id="ecosystem" className="scroll-mt-24 bg-[#f7f3e8] px-6 py-24 md:py-36">
        <div className="mx-auto max-w-6xl">
          <SectionHead
            kicker="The connecting layer"
            title="One connected agricultural ecosystem."
            lead="MaatiTrace is the digital layer that connects people, data and processes across the agricultural value chain — from the farm to the market."
          />

          <Stagger className="relative mt-16">
            <TimelineLine className="pointer-events-none absolute inset-x-[10%] top-10 hidden h-[3px] rounded-full bg-gradient-to-r from-emerald-300 via-emerald-500 to-emerald-300 md:block" />
            <div className="relative grid grid-cols-2 gap-x-6 gap-y-12 sm:grid-cols-3 md:grid-cols-5">
              {ECOSYSTEM.map((item, i) => (
                <Item key={item.title} className="group flex flex-col items-center text-center">
                  <Motion.div
                    whileHover={{ y: -6 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    className="relative grid h-20 w-20 place-items-center rounded-[22px] border border-emerald-900/10 bg-white shadow-[0_14px_34px_rgba(10,55,36,0.14)]"
                  >
                    <item.icon className="h-8 w-8 text-emerald-700 transition-transform duration-300 group-hover:scale-110" strokeWidth={2} />
                    <span className="absolute -right-2.5 -top-2.5 grid h-7 w-7 place-items-center rounded-full bg-[#0b3b2a] text-[12px] font-black text-[#b9e84d]">
                      {i + 1}
                    </span>
                  </Motion.div>
                  <h3 className="mt-4 text-lg font-black text-gray-900">{item.title}</h3>
                  <p className="mt-1 max-w-[160px] text-[13px] font-medium leading-snug text-gray-500">{item.desc}</p>
                </Item>
              ))}
            </div>
          </Stagger>

          <Reveal className="mx-auto mt-16 flex max-w-3xl flex-col items-center justify-center gap-4 rounded-[28px] bg-[#0b3b2a] px-8 py-6 text-white shadow-[0_26px_60px_rgba(8,49,33,0.28)] sm:flex-row sm:gap-8">
            <span className="text-xl font-black tracking-[0.2em]">MAATITRACE</span>
            <span className="hidden h-6 w-px bg-white/20 sm:block" />
            {[["Intelligence", Sparkles], ["Traceability", Waypoints], ["Sustainability", Leaf]].map(([label, Ic]) => (
              <span key={label} className="flex items-center gap-2 text-[15px] font-bold text-[#d7f0b6]">
                <Ic className="h-5 w-5" strokeWidth={2.2} />
                {label}
              </span>
            ))}
          </Reveal>
        </div>
      </section>

      {/* ── INTELLIGENCE ─────────────────────────────────────────────────── */}
      <section id="intelligence" className="relative scroll-mt-24 overflow-hidden bg-[#04271a] px-6 py-24 text-white md:py-36">
        <img src={IMG.intelBg} alt="" aria-hidden className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-20" loading="lazy" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#04271a] via-[#04271a]/85 to-[#04271a]/45" />
        <div className="relative mx-auto max-w-6xl">
          <SectionHead
            kicker="Intelligence"
            title={<>See the farm<br />from every angle.</>}
            lead="MaatiTrace brings multiple data sources together and turns raw agricultural data into meaningful intelligence."
            dark
          />

          <div className="mt-14 grid gap-10 lg:grid-cols-[0.8fr_2fr] lg:items-stretch">
            <Reveal className="flex flex-col justify-center">
              <p className="text-lg font-medium leading-relaxed text-white/80">
                Observe the field. Measure conditions. Understand change. Act with confidence.
              </p>
              <Link
                to="/our-method"
                className="mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-[#b9e84d] px-6 py-3.5 text-sm font-black text-[#17351f] transition-all hover:-translate-y-0.5 hover:bg-[#c9f45b]"
              >
                Learn More <ArrowRight className="h-4 w-4" />
              </Link>
            </Reveal>

            <Stagger className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
              {INTEL_SOURCES.map((c) => (
                <Item key={c.title} className="h-full">
                  <Motion.div
                    whileHover={{ y: -6 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    className="group relative flex h-full min-h-[16rem] flex-col justify-end overflow-hidden rounded-[24px] border border-white/15 p-5"
                  >
                    <img src={c.img} alt="" aria-hidden className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" loading="lazy" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#031e14] via-[#031e14]/55 to-transparent" />
                    <div className="relative">
                      <span className="inline-flex rounded-2xl bg-[#b9e84d] p-2.5 text-[#0b3b2a] shadow-lg">
                        <c.icon className="h-6 w-6" strokeWidth={2.2} />
                      </span>
                      <h3 className="mt-3 text-lg font-black uppercase tracking-wide text-white">{c.title}</h3>
                      <p className="mt-1 text-[13px] font-medium leading-snug text-white/85">{c.desc}</p>
                    </div>
                  </Motion.div>
                </Item>
              ))}
            </Stagger>
          </div>

          <Reveal className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-3 rounded-[22px] bg-white px-6 py-4 text-sm font-black text-[#0b3b2a] sm:justify-between">
            {INTEL_FLOW.map((f, i) => (
              <React.Fragment key={f.label}>
                <span className="flex items-center gap-2.5">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-emerald-100">
                    <f.icon className="h-4 w-4 text-emerald-700" strokeWidth={2.6} />
                  </span>
                  {f.label}
                </span>
                {i < INTEL_FLOW.length - 1 && <ArrowRight className="hidden h-4 w-4 text-emerald-300 sm:block" />}
              </React.Fragment>
            ))}
          </Reveal>
        </div>
      </section>

      {/* ── SOLUTIONS ────────────────────────────────────────────────────── */}
      <section id="solutions" className="scroll-mt-24 bg-white px-6 py-24 md:py-36">
        <div className="mx-auto max-w-6xl">
          <SectionHead
            kicker="Solutions for every user"
            title={<>One platform.<br />Built around your role.</>}
            lead="The same connected ecosystem, with the tools and intelligence each participant needs."
          />

          <Stagger className="mt-16 grid gap-6 md:grid-cols-3">
            {SOLUTIONS.map((s) => (
              <Item key={s.audience} className="h-full">
                <Motion.article
                  whileHover={{ y: -8 }}
                  transition={{ type: "spring", stiffness: 300, damping: 22 }}
                  className="group flex h-full flex-col overflow-hidden rounded-[28px] border border-gray-200 bg-white transition-shadow duration-300 hover:shadow-[0_30px_70px_rgba(0,0,0,0.12)]"
                >
                  <div className="relative h-48 w-full overflow-hidden">
                    <img src={s.img} alt="" aria-hidden className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy" />
                    <span className="absolute left-4 top-4 rounded-full bg-white/95 px-3 py-1 text-[11px] font-black uppercase tracking-[0.14em] text-emerald-700 shadow-sm">
                      {s.audience}
                    </span>
                  </div>
                  <div className="flex flex-1 flex-col p-7">
                    <h3 className="text-[26px] font-black leading-[1.05] tracking-tight text-gray-900">{s.title}</h3>
                    <p className="mt-2 text-sm font-medium text-gray-500">{s.desc}</p>
                    <ul className="mt-5 space-y-2.5">
                      {s.points.map((p) => (
                        <li key={p} className="flex items-start gap-2.5 text-sm font-medium text-gray-700">
                          <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emerald-100">
                            <Check className="h-3 w-3 text-emerald-700" strokeWidth={3} />
                          </span>
                          {p}
                        </li>
                      ))}
                    </ul>
                    <Link to={s.to} className="mt-6 inline-flex items-center gap-1.5 text-sm font-black text-emerald-700 transition-all hover:gap-2.5 hover:text-emerald-800">
                      {s.cta} <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </Motion.article>
              </Item>
            ))}
          </Stagger>
        </div>
      </section>

      {/* ── JOURNEY ──────────────────────────────────────────────────────── */}
      <section className="bg-[#f7f3e8] px-6 py-24 md:py-36">
        <div className="mx-auto max-w-5xl">
          <SectionHead
            kicker="Traceability"
            title="Every product has a story."
            lead="From the field to the final buyer, MaatiTrace creates a verifiable digital trail of every step."
          />
          <div className="relative mt-16">
            <TimelineLine className="pointer-events-none absolute inset-x-[8%] top-8 hidden h-1 rounded-full bg-gradient-to-r from-emerald-300 via-emerald-500 to-emerald-300 md:block" />
            <Stagger className="relative grid grid-cols-2 gap-x-4 gap-y-12 sm:grid-cols-3 md:grid-cols-6">
              {JOURNEY.map((j, i) => (
                <Item key={j.title} className="flex flex-col items-center text-center">
                  <div className="relative grid h-16 w-16 place-items-center rounded-2xl border-2 border-emerald-600 bg-white shadow-[0_10px_24px_rgba(10,55,36,0.12)]">
                    <j.icon className="h-7 w-7 text-emerald-700" strokeWidth={2} />
                    <span className="absolute -bottom-2.5 grid h-6 w-6 place-items-center rounded-full bg-emerald-600 text-[12px] font-black text-white">
                      {i + 1}
                    </span>
                  </div>
                  <h3 className="mt-5 text-lg font-black text-gray-900">{j.title}</h3>
                  <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-gray-400">{j.sub}</p>
                </Item>
              ))}
            </Stagger>
          </div>
        </div>
      </section>

      {/* ── TRACEABILITY DETAIL ──────────────────────────────────────────── */}
      <section id="traceability" className="scroll-mt-24 bg-white px-6 py-24 md:py-36">
        <div className="mx-auto max-w-6xl">
          <SectionHead
            kicker="Traceability"
            title="Know where it came from."
            lead="Connect a product or batch back to its agricultural origin and the evidence behind it."
          />
          <div className="mt-14 grid gap-12 md:grid-cols-[1fr_0.8fr] md:items-center">
            <Stagger className="grid gap-3">
              {TRACE_ITEMS.map((t) => (
                <Item key={t.label}>
                  <Motion.div
                    whileHover={{ x: 6 }}
                    transition={{ type: "spring", stiffness: 300, damping: 22 }}
                    className="flex items-center gap-4 rounded-2xl border border-gray-200 bg-[#f4f6f0] px-5 py-4"
                  >
                    <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white shadow-sm">
                      <t.icon className="h-5 w-5 text-emerald-700" strokeWidth={2.2} />
                    </span>
                    <div>
                      <b className="text-sm font-black uppercase tracking-wide text-gray-900">{t.label}</b>
                      <small className="block text-xs font-medium text-gray-500">{t.desc}</small>
                    </div>
                  </Motion.div>
                </Item>
              ))}
            </Stagger>

            <Reveal>
              <Motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
                className="rounded-[28px] bg-[#0b3b2a] p-8 text-center text-white shadow-[0_28px_60px_rgba(8,49,33,0.28)]"
              >
                <div className="mx-auto mb-4 grid h-44 w-44 place-items-center rounded-2xl bg-white">
                  <QrCode className="h-32 w-32 text-[#0b3b2a]" strokeWidth={1.4} />
                </div>
                <b className="text-lg font-black">Scan the product story</b>
                <p className="mt-1.5 text-xs font-medium text-white/65">
                  Prototype visual — links to the live MaatiTrace traceability experience.
                </p>
              </Motion.div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── SUSTAINABILITY ───────────────────────────────────────────────── */}
      <section id="sustainability" className="scroll-mt-24 bg-[#eaf1e4] px-6 py-24 md:py-36">
        <div className="mx-auto max-w-6xl">
          <SectionHead
            kicker="Sustainability"
            title={<>Measure. Improve.<br />Prove. Grow.</>}
          />
          <div className="mt-14 grid gap-12 md:grid-cols-2 md:items-center">
            <Reveal>
              <Motion.div
                whileHover={{ scale: 1.02 }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                className="h-[400px] rounded-[28px] bg-cover bg-center shadow-[0_24px_60px_rgba(8,47,31,0.25)]"
                style={{ backgroundImage: `linear-gradient(transparent, rgba(8,47,31,0.42)), url(${IMG.sustain})` }}
              />
            </Reveal>
            <div>
              <Reveal>
                <p className="text-lg font-medium leading-relaxed text-gray-600">
                  Build evidence-based sustainability records across farms, production and value chains.
                </p>
              </Reveal>
              <Stagger className="mt-7 grid grid-cols-1 gap-3.5 sm:grid-cols-2">
                {SUSTAIN.map((s) => (
                  <Item key={s.title}>
                    <Motion.div
                      whileHover={{ y: -5 }}
                      transition={{ type: "spring", stiffness: 300, damping: 20 }}
                      className="h-full rounded-[20px] bg-white p-6 shadow-[0_12px_30px_rgba(10,55,36,0.08)]"
                    >
                      <span className="inline-flex rounded-xl bg-emerald-100 p-2.5">
                        <s.icon className="h-6 w-6 text-emerald-700" strokeWidth={2.2} />
                      </span>
                      <h3 className="mt-4 text-lg font-black text-gray-900">{s.title}</h3>
                      <p className="mt-1 text-[13px] font-medium text-gray-500">{s.desc}</p>
                    </Motion.div>
                  </Item>
                ))}
              </Stagger>
            </div>
          </div>
        </div>
      </section>

      {/* ── IMPACT ───────────────────────────────────────────────────────── */}
      <section className="bg-white px-6 py-24 md:py-36">
        <div className="mx-auto max-w-6xl">
          <SectionHead
            kicker="Built for impact. Trusted by partners."
            title="Intelligence that creates value."
          />
          <Stagger className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {IMPACT.map((item) => (
              <Item key={item.title} className="h-full">
                <Motion.div
                  whileHover={{ y: -6 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="h-full rounded-[22px] border border-gray-200 p-7"
                >
                  <span className="inline-flex rounded-2xl bg-emerald-100 p-3">
                    <item.icon className="h-6 w-6 text-emerald-700" strokeWidth={2.2} />
                  </span>
                  <h3 className="mt-5 text-lg font-black text-gray-900">{item.title}</h3>
                  <p className="mt-1.5 text-[13px] font-medium text-gray-500">{item.desc}</p>
                </Motion.div>
              </Item>
            ))}
          </Stagger>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────── */}
      <section id="demo" className="relative scroll-mt-24 overflow-hidden px-6 py-28 text-center text-white md:py-36">
        <img src={IMG.ctaBg} alt="" aria-hidden className="pointer-events-none absolute inset-0 h-full w-full object-cover" loading="lazy" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#04261a]/95 to-[#04261a]/60" />
        <div className="relative mx-auto max-w-3xl">
          <Reveal className="space-y-6">
            <span className="inline-flex items-center gap-3 text-[12px] font-extrabold uppercase tracking-[0.3em] text-[#b9e84d]">
              <span className="h-[3px] w-8 rounded-full bg-[#b9e84d]" />
              Start the journey
            </span>
            <h2 className="text-[34px] font-black leading-[0.98] tracking-[-0.02em] sm:text-5xl md:text-6xl">
              Ready to connect your value chain?
            </h2>
            <p className="mx-auto max-w-xl text-base leading-relaxed text-white/75">
              Let's build a smarter, more traceable and sustainable agricultural future together.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link to="/register"
                className="inline-flex items-center gap-2 rounded-2xl bg-[#b9e84d] px-8 py-4 text-sm font-black text-[#17351f] transition-all hover:-translate-y-0.5 hover:bg-[#c9f45b]">
                Get Started <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/login"
                className="inline-flex items-center gap-2 rounded-2xl border border-white/40 px-7 py-4 text-sm font-bold text-white transition-all hover:bg-white/10">
                Sign In
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── FOOTER (unchanged) ───────────────────────────────────────────── */}
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
            <Link to="/plans" className="hover:text-gray-900 transition-colors">Plans</Link>
            <Link to="/login" className="hover:text-gray-900 transition-colors">Sign In</Link>
          </div>
          <p className="text-[10px] text-gray-300 w-full md:w-auto text-center md:text-right">© 2026 MaatiTrace. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
