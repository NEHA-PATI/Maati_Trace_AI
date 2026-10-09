import React from "react";
import { Link } from "react-router-dom";
import PublicNav from "@/components/layout/PublicNav";
import { 
  Droplets, Leaf, Bug, Trees, CloudRain, BarChart3, 
  Users, FileText, ArrowRight, Hexagon, ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

const USE_CASES = [
  {
    icon: Droplets,
    title: "Water Stress Detection",
    subtitle: "Moisture deficit before visible wilting",
    description: "Normalized Difference Moisture Index (NDMI) computed per H3 cell identifies sub-field moisture variation. When readings drop below threshold for consecutive scenes, stress alerts fire to the farmer and FPO manager. No guesswork — the satellite measures what the soil cannot hide.",
    metrics: ["NDMI threshold < 0.2", "3-scene consecutive drop", "Per-cell resolution"],
    color: "text-blue-600",
    bg: "bg-blue-500/10",
  },
  {
    icon: Leaf,
    title: "Crop Health Monitoring",
    subtitle: "Vegetation signal across growth cycles",
    description: "NDVI trajectories tracked from sowing to harvest. Each H3 cell carries its own temporal profile. Anomalous cells — those deviating from the farm's average curve — are flagged. The system doesn't guess the cause; it shows where the problem is.",
    metrics: ["NDVI temporal profile", "Per-cell deviation scoring", "Growth stage alignment"],
    color: "text-primary",
    bg: "bg-primary/10",
  },
  {
    icon: Bug,
    title: "Pest & Disease Risk",
    subtitle: "Environmental conditions cross-referenced",
    description: "Temperature, humidity, and vegetation stress patterns overlaid with known pest cycle calendars. When conditions match risk windows for common Odisha pests — rice blast, brown planthopper, stem borer — the system elevates the notification to priority.",
    metrics: ["Temperature correlation", "Humidity thresholds", "Crop-specific pest calendars"],
    color: "text-amber-600",
    bg: "bg-amber-500/10",
  },
  {
    icon: Trees,
    title: "Plantation Monitoring",
    subtitle: "Long-cycle canopy tracking over seasons",
    description: "For cashew, mango, and coconut plantations, NDVI and canopy density are tracked across years. Growth rate measurements, gap detection in planting rows, and seasonal canopy variation — all computed from satellite scenes without field visits.",
    metrics: ["Multi-year NDVI tracking", "Canopy gap detection", "Seasonal comparison"],
    color: "text-green-700",
    bg: "bg-green-500/10",
  },
  {
    icon: CloudRain,
    title: "Flood & Waterlogging Risk",
    subtitle: "Excess moisture before damage sets in",
    description: "During monsoon, moisture indices spike before visible waterlogging. The system detects abnormal moisture accumulation in low-lying H3 cells and alerts before crop damage becomes irreversible. Particularly relevant for Odisha's flood-prone deltas.",
    metrics: ["Monsoon moisture spikes", "Topographic risk overlay", "48-hour early warning"],
    color: "text-cyan-600",
    bg: "bg-cyan-500/10",
  },
  {
    icon: BarChart3,
    title: "Yield Intelligence",
    subtitle: "Historical NDVI correlated with harvest data",
    description: "By matching NDVI trajectory patterns against known yield outcomes from previous seasons, the system projects harvest ranges per farm. Not a prediction — a range estimate grounded in satellite-measured crop vigor.",
    metrics: ["3-season correlation", "NDVI-yield regression", "Range-based estimates"],
    color: "text-purple-600",
    bg: "bg-purple-500/10",
  },
  {
    icon: Users,
    title: "FPO Coverage Intelligence",
    subtitle: "Organizational visibility across geography",
    description: "FPO managers see real-time farmer distribution, block-wise coverage gaps, pending registrations, and collective health summaries. The dashboard surfaces where the FPO's support is needed most — not where it's already strong.",
    metrics: ["Block-wise density", "Coverage gap scoring", "Priority alerting"],
    color: "text-violet-700",
    bg: "bg-violet-100",
  },
  {
    icon: FileText,
    title: "Digital Product Passport",
    subtitle: "Verifiable chain from soil to shelf",
    description: "Every farm parcel carries a complete digital record: registered boundary, satellite scene history, health indices over time, farmer identity link, FPO association. This chain becomes the foundation for traceability, credit scoring, and insurance verification.",
    metrics: ["Boundary verification", "Satellite history chain", "Identity-linked records"],
    color: "text-amber-700",
    bg: "bg-amber-100",
  },
];

const CARD_TINTS = [
  "bg-sky-50 border-t-sky-500",
  "bg-lime-50 border-t-lime-600",
  "bg-amber-50 border-t-amber-500",
  "bg-emerald-50 border-t-emerald-600",
  "bg-cyan-50 border-t-cyan-500",
  "bg-indigo-50 border-t-indigo-500",
  "bg-fuchsia-50 border-t-fuchsia-500",
  "bg-rose-50 border-t-rose-500",
];

const ICON_TINTS = [
  "bg-blue-600 text-white",
  "bg-green-700 text-white",
  "bg-amber-600 text-white",
  "bg-emerald-700 text-white",
  "bg-cyan-600 text-white",
  "bg-purple-600 text-white",
  "bg-violet-600 text-white",
  "bg-orange-600 text-white",
];

export default function UseCases() {
  return (
    <div className="min-h-screen bg-background">
      <PublicNav />

      <div className="mx-auto w-full max-w-none px-4 py-12 pt-24 md:px-8 md:py-16 md:pt-28 lg:px-12 xl:px-16">
        <div className="relative min-h-[220px] overflow-hidden rounded-2xl border border-primary/40 bg-[#f1f7ed] bg-[url('/image.png')] bg-cover bg-center px-6 py-6 text-center shadow-[0_14px_34px_-24px_rgba(51,73,42,0.55)] md:min-h-[260px] md:px-10 md:py-7">
          <div className="absolute inset-0 bg-white/35" />
          <div className="relative mx-auto max-w-4xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-white px-3 py-1 text-[9px] font-display font-semibold uppercase tracking-[0.2em] text-primary shadow-sm"><span className="h-1.5 w-1.5 rounded-full bg-primary" /> Field applications</span>
            <h1 className="mt-3 text-2xl font-display font-bold leading-tight tracking-tight text-foreground md:text-4xl lg:text-5xl">From satellite signal to field action</h1>
            <p className="mx-auto mt-2 max-w-2xl text-xs leading-5 text-muted-foreground md:text-sm">MaatiTrace turns registered boundaries, H3 grid cells, satellite scenes, and computed indices into decisions farmers and FPOs can act on.</p>
          </div>
        </div>

        <div className="my-8 grid grid-cols-2 divide-x divide-border overflow-hidden rounded-xl border border-border bg-card md:grid-cols-4">
          {[["08", "active use cases"], ["H3", "cell-level view"], ["NDVI", "crop health signal"], ["48h", "early warning"]].map(([value, label]) => (<div key={label} className="px-4 py-5 text-center md:px-6"><p className="text-xl font-display font-bold text-primary md:text-2xl">{value}</p><p className="mt-1 text-[9px] font-display uppercase tracking-wider text-muted-foreground md:text-[10px]">{label}</p></div>))}
        </div>

        <div className="mb-5 flex items-end justify-between gap-4"><div><p className="text-xs font-display font-semibold uppercase tracking-[0.18em] text-primary">The intelligence layer</p><h2 className="mt-1 text-xl font-display font-bold text-foreground md:text-2xl">Built for decisions in the field</h2></div><span className="hidden rounded-full bg-muted px-3 py-1 text-[10px] font-display uppercase tracking-wider text-muted-foreground sm:inline-flex">Data-backed monitoring</span></div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {USE_CASES.map((uc, i) => {
            const Icon = uc.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.04 }}
                className={`group overflow-hidden rounded-2xl border border-white/70 border-t-4 shadow-[0_8px_22px_-16px_rgba(29,33,23,0.55)] transition-all duration-300 hover:-translate-y-1 hover:border-white hover:shadow-[0_18px_30px_-16px_rgba(29,33,23,0.45)] ${CARD_TINTS[i]}`}
              >
                <div className="flex h-full flex-col p-7"><div className="mb-5 flex items-start justify-between gap-4"><div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl shadow-sm ${ICON_TINTS[i]}`}><Icon className="h-7 w-7" /></div><span className="rounded-full bg-white/70 px-2.5 py-1 text-[9px] font-display font-semibold uppercase tracking-wider text-foreground/60">Live signal</span></div><h3 className="text-lg font-display font-bold text-foreground">{uc.title}</h3><p className="mt-1 text-[10px] font-display uppercase tracking-wider text-foreground/60">{uc.subtitle}</p><p className="mt-4 flex-1 text-sm leading-6 text-foreground/75">{uc.description}</p><div className="mt-5 flex flex-wrap gap-2 border-t border-black/10 pt-4">
                      {uc.metrics.map((m, j) => (
                        <span key={j} className="inline-flex items-center rounded-full bg-white/75 px-2.5 py-1 text-[9px] font-display uppercase tracking-wider text-muted-foreground shadow-sm">
                          {m}
                        </span>
                      ))}
                    </div></div>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-12 rounded-xl border border-primary/20 bg-primary/[0.04] px-6 py-8 text-center md:mt-14 md:px-10"><p className="text-lg font-display font-semibold text-foreground">Ready to see your land through a new lens?</p><p className="mt-2 text-sm text-muted-foreground">Register a parcel and start building your field intelligence layer.</p>
          <Link to="/register">
            <Button size="lg" className="mt-5 h-12 rounded-lg px-8 text-sm font-display uppercase tracking-wider">
              Register Your Land <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
