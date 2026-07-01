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
    color: "text-foreground",
    bg: "bg-muted",
  },
  {
    icon: FileText,
    title: "Digital Product Passport",
    subtitle: "Verifiable chain from soil to shelf",
    description: "Every farm parcel carries a complete digital record: registered boundary, satellite scene history, health indices over time, farmer identity link, FPO association. This chain becomes the foundation for traceability, credit scoring, and insurance verification.",
    metrics: ["Boundary verification", "Satellite history chain", "Identity-linked records"],
    color: "text-foreground",
    bg: "bg-muted",
  },
];

export default function UseCases() {
  return (
    <div className="min-h-screen bg-background">
      <PublicNav />

      <div className="max-w-5xl mx-auto px-4 md:px-6 py-16 pt-28">
        <div className="text-center mb-16">
          <span className="text-[10px] font-display uppercase tracking-[0.3em] text-muted-foreground">Field Applications</span>
          <h1 className="text-3xl md:text-4xl font-display font-bold text-foreground mt-3 tracking-tight">What MaatiTrace Monitors</h1>
          <p className="text-sm text-muted-foreground mt-3 max-w-lg mx-auto">Every use case is backed by the same pipeline: registered boundaries, H3 grid cells, satellite scenes, and computed indices. No claims without data.</p>
        </div>

        <div className="space-y-6">
          {USE_CASES.map((uc, i) => {
            const Icon = uc.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="bg-card border border-border rounded-sm overflow-hidden hover:border-primary/20 transition-colors"
              >
                <div className="grid grid-cols-1 md:grid-cols-4 gap-0">
                  <div className={`${uc.bg} p-6 flex flex-col justify-center items-center text-center md:items-start md:text-left`}>
                    <Icon className={`w-8 h-8 ${uc.color} mb-3`} />
                    <h3 className="text-base font-display font-bold text-foreground">{uc.title}</h3>
                    <p className="text-[10px] text-muted-foreground mt-1 font-display uppercase tracking-wider">{uc.subtitle}</p>
                  </div>
                  <div className="md:col-span-3 p-6">
                    <p className="text-sm text-muted-foreground leading-relaxed mb-4">{uc.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {uc.metrics.map((m, j) => (
                        <span key={j} className="inline-flex items-center px-2 py-1 bg-muted rounded-sm text-[9px] font-display uppercase tracking-wider text-muted-foreground">
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="text-center mt-16">
          <Link to="/register">
            <Button size="lg" className="h-12 px-8 text-sm font-display uppercase tracking-wider rounded-sm">
              Register Your Land <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}