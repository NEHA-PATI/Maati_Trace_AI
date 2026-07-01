import React, { useRef } from "react";
import { Link } from "react-router-dom";
import PublicNav from "@/components/layout/PublicNav";
import { 
  Hexagon, MapPin, User, Layers, Grid3X3, Satellite, 
  BarChart3, Lightbulb, ArrowRight, ChevronDown, ArrowDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, useScroll, useTransform, useInView } from "framer-motion";

const PIPELINE_STEPS = [
  {
    num: "01",
    icon: MapPin,
    title: "Location Validation",
    desc: "Every registration begins with administrative verification. State → District → Block boundaries sourced from Survey of India data. The system confirms the location exists before anything proceeds.",
    detail: "GET /v1/states → GET /v1/districts → GET /v1/blocks → POST /v1/location/validate",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg",
  },
  {
    num: "02",
    icon: User,
    title: "Farmer & FPO Registration",
    desc: "Farmer identity linked to an FPO. Name, village, block, contact, Aadhaar reference. The farmer is not anonymous — they belong to an organisation, a geography, and a record system.",
    detail: "POST /v1/farmers → POST /v1/fpos",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/36_vcukad.jpg",
  },
  {
    num: "03",
    icon: Layers,
    title: "Farm Boundary Registration",
    desc: "Polygon coordinates define the farm boundary — either drawn on a map or entered from survey records. The actual shape of the land, however irregular, becomes the registered boundary. Area calculated from vertices.",
    detail: "POST /v1/farms/register → boundary stored as GeoJSON polygon",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg",
  },
  {
    num: "04",
    icon: Grid3X3,
    title: "H3 Hexagonal Grid Generation",
    desc: "Uber H3 cells generated at resolution 10 inside the farm boundary. Each hexagonal cell (~15,000 m²) becomes an independent sensing unit. The farm is no longer one reading — it's a grid of readings.",
    detail: "Boundary → H3 cell IDs at resolution 10 → Each cell: independent raster sample",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg",
  },
  {
    num: "05",
    icon: Satellite,
    title: "Satellite Scene Discovery",
    desc: "STAC catalog queried for Sentinel-2 scenes covering the farm's geographic extent. The system searches for the most recent acquisition with acceptable cloud cover. Scene metadata — date, provider, cloud percentage — logged.",
    detail: "POST /v1/stac/search → returns scene ID, date, cloud_cover, geometry",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/32_nvof1e.jpg",
  },
  {
    num: "06",
    icon: BarChart3,
    title: "Raster Index Calculation",
    desc: "Sentinel-2 bands processed per H3 cell. NDVI (vegetation), NDMI (moisture), BSI (bare soil) computed. Cloud-masked pixels excluded — only valid spectral readings survive. Each cell gets its own set of indices.",
    detail: "POST /v1/raster/sentinel2/indices/preview → per-cell: ndvi, moisture, bare_soil, valid_pixels",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/35_nxcqrp.jpg",
  },
  {
    num: "07",
    icon: Hexagon,
    title: "Field Intelligence Assembly",
    desc: "Per-cell analytics aggregated into farm-level health signals. Stress zones identified from deviation analysis. Temporal change tracked across scenes. The farm now carries a living intelligence record.",
    detail: "Cell aggregation → farm averages → deviation scoring → temporal delta",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/34_sgalr8.jpg",
  },
  {
    num: "08",
    icon: Lightbulb,
    title: "Actionable Insight Delivery",
    desc: "Predictions, alerts, and recommendations pushed to farmer and FPO. Water stress warnings, pest risk windows, yield projections — all traceable back to specific H3 cells and specific satellite scenes. Nothing ungrounded.",
    detail: "Notification → priority routing → farmer/FPO dashboard → land intelligence page",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/37_e3xyru.jpg",
  },
];

function StepBlock({ step, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
      className="relative"
    >
      {/* Vertical connector */}
      {index < PIPELINE_STEPS.length - 1 && (
        <div className="absolute left-6 md:left-8 top-full w-px h-8 bg-gradient-to-b from-primary/40 to-transparent z-10" />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-0 bg-card border border-border rounded-sm overflow-hidden hover:border-primary/20 transition-colors">
        {/* Image */}
        <div className={`lg:col-span-2 relative overflow-hidden ${index % 2 === 1 ? "lg:order-2" : ""}`}>
          <img
            src={step.img}
            alt={step.title}
            className="w-full h-56 lg:h-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
        </div>

        {/* Content */}
        <div className={`lg:col-span-3 p-6 lg:p-8 flex flex-col justify-center ${index % 2 === 1 ? "lg:order-1" : ""}`}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-sm bg-primary/10 flex items-center justify-center">
              <step.icon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <span className="text-[9px] font-display uppercase tracking-[0.3em] text-muted-foreground">Stage {step.num}</span>
              <h3 className="text-lg font-display font-bold text-foreground tracking-tight">{step.title}</h3>
            </div>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed mb-4">{step.desc}</p>
          <div className="px-3 py-2 bg-muted/50 border border-border rounded-sm">
            <span className="text-[9px] font-display uppercase tracking-widest text-muted-foreground block mb-0.5">Technical Path</span>
            <code className="text-[10px] font-mono text-foreground/80">{step.detail}</code>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function OurMethod() {
  return (
    <div className="min-h-screen bg-background">
      <PublicNav />

      {/* Hero */}
      <section className="py-20 px-4 md:px-6 pt-28 text-center bg-muted/30 topo-texture border-b border-border">
        <span className="text-[10px] font-display uppercase tracking-[0.3em] text-muted-foreground">From Land to Intelligence</span>
        <h1 className="text-3xl md:text-5xl font-display font-bold text-foreground mt-4 tracking-tight">The MaatiTrace Method</h1>
        <p className="text-sm text-muted-foreground mt-4 max-w-xl mx-auto leading-relaxed">
          Eight stages transform a piece of land into a living intelligence record. Each stage is verified. Each output is traceable. Nothing is assumed.
        </p>
        <motion.div animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 2 }} className="mt-8">
          <ArrowDown className="w-5 h-5 text-muted-foreground mx-auto" />
        </motion.div>
      </section>

      {/* Pipeline */}
      <section className="max-w-5xl mx-auto px-4 md:px-6 py-16 space-y-8">
        {PIPELINE_STEPS.map((step, i) => (
          <StepBlock key={step.num} step={step} index={i} />
        ))}
      </section>

      {/* CTA */}
      <section className="py-16 px-4 md:px-6 text-center border-t border-border">
        <h2 className="text-2xl font-display font-bold text-foreground tracking-tight mb-4">Ready to Register Your Land?</h2>
        <p className="text-sm text-muted-foreground mb-6">Start with location validation. End with satellite-backed intelligence.</p>
        <Link to="/register">
          <Button size="lg" className="h-12 px-8 text-sm font-display uppercase tracking-wider rounded-sm">
            Get Started <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
      </section>
    </div>
  );
}