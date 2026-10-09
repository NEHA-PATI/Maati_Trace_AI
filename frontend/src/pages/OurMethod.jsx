import { useRef } from "react";
import { Link } from "react-router-dom";
import PublicNav from "@/components/layout/PublicNav";
import {
  Hexagon,
  MapPin,
  User,
  Layers,
  Grid3X3,
  Satellite,
  BarChart3,
  Lightbulb,
  ArrowRight,
  ArrowDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, useInView } from "framer-motion";

const PIPELINE_STEPS = [
  {
    num: "01",
    icon: MapPin,
    title: "Location Validation",
    desc: "Every registration begins with administrative verification. State -> District -> Block boundaries sourced from Survey of India data. The system confirms the location exists before anything proceeds.",
    detail: "GET /api/location/states -> GET /api/location/districts -> GET /api/location/blocks -> POST /api/location/validate",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464056/30_m27lfc.jpg",
  },
  {
    num: "02",
    icon: User,
    title: "Farmer & FPO Registration",
    desc: "Farmer identity linked to an FPO. Name, village, block, contact, Aadhaar reference. The farmer is not anonymous - they belong to an organisation, a geography, and a record system.",
    detail: "POST /api/farmers -> POST /api/fpos",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/36_vcukad.jpg",
  },
  {
    num: "03",
    icon: Layers,
    title: "Farm Boundary Registration",
    desc: "Polygon coordinates define the farm boundary - either drawn on a map or entered from survey records. The actual shape of the land, however irregular, becomes the registered boundary. Area calculated from vertices.",
    detail: "POST /api/farms/register -> boundary stored as GeoJSON polygon",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/33_eevoop.jpg",
  },
  {
    num: "04",
    icon: Grid3X3,
    title: "H3 Hexagonal Grid Generation",
    desc: "Uber H3 cells generated at resolution 10 inside the farm boundary. Each hexagonal cell (~15,000 m2) becomes an independent sensing unit. The farm is no longer one reading - it's a grid of readings.",
    detail: "Boundary -> H3 cell IDs at resolution 10 -> Each cell: independent raster sample",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg",
  },
  {
    num: "05",
    icon: Satellite,
    title: "Satellite Scene Discovery",
    desc: "STAC catalog queried for Sentinel-2 scenes covering the farm's geographic extent. The system searches for the most recent acquisition with acceptable cloud cover. Scene metadata - date, provider, cloud percentage - logged.",
    detail: "POST /api/stac/search -> returns scene ID, date, cloud_cover, geometry",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/32_nvof1e.jpg",
  },
  {
    num: "06",
    icon: BarChart3,
    title: "Raster Index Calculation",
    desc: "Sentinel-2 bands processed per H3 cell. NDVI (vegetation), NDMI (moisture), BSI (bare soil) computed. Cloud-masked pixels excluded - only valid spectral readings survive. Each cell gets its own set of indices.",
    detail: "POST /api/raster/sentinel2/indices/preview -> per-cell: ndvi, moisture, bare_soil, valid_pixels",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/35_nxcqrp.jpg",
  },
  {
    num: "07",
    icon: Hexagon,
    title: "Field Intelligence Assembly",
    desc: "Per-cell analytics aggregated into farm-level health signals. Stress zones identified from deviation analysis. Temporal change tracked across scenes. The farm now carries a living intelligence record.",
    detail: "Cell aggregation -> farm averages -> deviation scoring -> temporal delta",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/34_sgalr8.jpg",
  },
  {
    num: "08",
    icon: Lightbulb,
    title: "Actionable Insight Delivery",
    desc: "Predictions, alerts, and recommendations pushed to farmer and FPO. Water stress warnings, pest risk windows, yield projections - all traceable back to specific H3 cells and specific satellite scenes. Nothing ungrounded.",
    detail: "Notification -> priority routing -> farmer/FPO dashboard -> land intelligence page",
    img: "https://res.cloudinary.com/dkst917dg/image/upload/v1780464057/37_e3xyru.jpg",
  },
];

function StepBlock({ step, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: false, margin: "-80px" });
  const iconTones = [
    "bg-[#E1F1D6] text-[#4B6B3A]",
    "bg-[#E6F0E8] text-[#2E6B52]",
    "bg-[#FFF0D5] text-[#9A6723]",
    "bg-[#E8E6F4] text-[#5B568E]",
    "bg-[#DDEEF4] text-[#2B6A80]",
    "bg-[#F4E5D9] text-[#9A5731]",
    "bg-[#E5F0D8] text-[#557A36]",
    "bg-[#F6E5B9] text-[#8A6424]",
  ];

  return (
    <motion.div
      ref={ref}
      initial={{
        opacity: 0,
        x: index % 2 === 0 ? -90 : 90,
        y: 24,
        scale: 0.96,
      }}
      animate={isInView
        ? { opacity: 1, x: 0, y: 0, scale: 1 }
        : { opacity: 0, x: index % 2 === 0 ? -90 : 90, y: 24, scale: 0.96 }}
      transition={{
        duration: 0.7,
        delay: index * 0.06,
        ease: [0.16, 1, 0.3, 1],
      }}
      className="relative"
    >
      {index < PIPELINE_STEPS.length - 1 && (
        <div className="absolute left-6 md:left-8 top-full w-px h-8 bg-gradient-to-b from-primary/40 to-transparent z-10" />
      )}

      <div className="group grid grid-cols-1 gap-0 overflow-hidden rounded-2xl border border-border bg-card transition-colors hover:border-primary/20 lg:grid-cols-5">
        <div className={`lg:col-span-2 relative overflow-hidden ${index % 2 === 1 ? "lg:order-2" : ""}`}>
          <img
            src={step.img}
            alt={step.title}
            className="w-full h-56 lg:h-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
        </div>

        <div className={`lg:col-span-3 flex flex-col justify-center p-5 lg:p-7 ${index % 2 === 1 ? "lg:order-1" : ""}`}>
          <div className="mb-3.5 flex items-center gap-3">
            <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-sm transition-transform duration-300 group-hover:scale-105 ${iconTones[index]}`}>
              <step.icon className="h-5 w-5" strokeWidth={1.8} />
            </div>
            <div>
              <span className="text-[11px] font-display font-semibold uppercase tracking-[0.3em] text-muted-foreground">Stage {step.num}</span>
              <h3 className="text-lg font-display font-bold leading-tight tracking-tight text-foreground lg:text-xl">{step.title}</h3>
            </div>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground lg:text-base lg:leading-7">{step.desc}</p>
        </div>
      </div>
    </motion.div>
  );
}

export default function OurMethod() {
  return (
    <div className="min-h-screen bg-background">
      <PublicNav />

      <section className="px-4 py-8 pt-20 text-center bg-muted/30 topo-texture border-b border-border md:px-6 md:py-10 md:pt-20">
        <span className="text-[10px] font-display uppercase tracking-[0.3em] text-muted-foreground">From Land to Intelligence</span>
        <h1 className="mt-3 text-3xl font-display font-bold tracking-tight text-foreground md:mt-4 md:text-5xl">The MaatiTrace Method</h1>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground md:mt-4">
          Eight stages transform a piece of land into a living intelligence record. Each stage is verified. Each output is traceable. Nothing is assumed.
        </p>
        <motion.div animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 2 }} className="mt-4 hidden md:block">
          <ArrowDown className="w-5 h-5 text-muted-foreground mx-auto" />
        </motion.div>
      </section>

      <section className="mx-auto w-full max-w-none space-y-8 px-4 py-8 md:px-8 md:py-8 lg:px-12 xl:px-16">
        {PIPELINE_STEPS.map((step, i) => (
          <StepBlock key={step.num} step={step} index={i} />
        ))}
      </section>

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
