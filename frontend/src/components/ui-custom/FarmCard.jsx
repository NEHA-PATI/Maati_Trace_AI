import React from "react";
import { Link } from "react-router-dom";
import { MapPin, Grid2x2, Leaf, Droplets, Wheat, Check, Clock, ChevronRight } from "lucide-react";
import FarmGridSnapshot from "@/components/ui-custom/FarmGridSnapshot";

function vegetationLabel(ndvi) {
  if (!ndvi || ndvi <= 0) return "Checking";
  if (ndvi > 0.5) return "Healthy";
  if (ndvi > 0.3) return "Okay";
  return "Needs care";
}

function moistureLabel(value) {
  if (!value || value <= 0) return "Checking";
  if (value > 0.4) return "Good";
  if (value > 0.2) return "Okay";
  return "Low";
}

export default function FarmCard({ farm }) {
  const {
    id = "MF-0042",
    village = "Baliguali",
    block = "Puri Sadar",
    district = "Puri",
    area = 2.4,
    crop = "Paddy (Kharif)",
    ndvi = 0.62,
    moisture = 0.44,
    status = "verified",
    h3Count = 18,
    farmName = "Registered farm",
    polygon = [],
  } = farm || {};

  const verified = status === "verified";
  const cropLabel = !crop || crop === "Crop data pending" ? "Add now" : crop;
  const location = [village, block, district].filter(Boolean).join(", ");

  return (
    <Link to={`/land/${id}`} className="mt-surface block">
      <div className="overflow-hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white transition-shadow hover:shadow-md">
        <div
          className={`flex items-center justify-between px-3.5 py-2.5 ${
            verified ? "bg-[var(--mt-leaf-tint)]" : "bg-[var(--mt-gold-tint)]"
          }`}
        >
          <span
            className={`flex items-center gap-1.5 text-[12px] font-bold ${
              verified ? "text-[var(--mt-leaf-deep)]" : "text-[var(--mt-gold-text)]"
            }`}
          >
            <Grid2x2 className="h-4 w-4" strokeWidth={2} />
            {h3Count} map cells
          </span>
          <span className="flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[11px] font-bold">
            {verified ? (
              <>
                <Check className="h-3 w-3 text-[var(--mt-leaf-deep)]" strokeWidth={3} />
                <span className="text-[var(--mt-leaf-deep)]">Verified</span>
              </>
            ) : (
              <>
                <Clock className="h-3 w-3 text-[var(--mt-gold-text)]" strokeWidth={2.6} />
                <span className="text-[var(--mt-gold-text)]">Checking</span>
              </>
            )}
          </span>
        </div>

        <FarmGridSnapshot farmId={id} polygon={polygon} tone={verified ? "good" : "wait"} className="h-32 w-full" />

        <div className="p-4">
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-[16px] font-extrabold text-[var(--mt-ink)]">{farmName}</span>
            <span className="text-[16px] font-extrabold text-[var(--mt-ink)]">
              {Number(area).toFixed(2)}
              <span className="ml-0.5 text-[11px] font-bold text-[var(--mt-ink-faint)]">ac</span>
            </span>
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-[12.5px] font-semibold text-[var(--mt-ink-soft)]">
            <MapPin className="h-3.5 w-3.5 text-[var(--mt-clay)]" strokeWidth={2.2} />
            {location}
          </div>

          <div className="mt-3 flex gap-2">
            <div className="flex flex-1 flex-col gap-1 rounded-[10px] bg-[var(--mt-leaf-tint)] px-2 py-2">
              <span className="flex items-center gap-1 text-[10px] font-extrabold text-[var(--mt-leaf-deep)]">
                <Leaf className="h-3 w-3" strokeWidth={2.4} />
                Health
              </span>
              <span className="text-[11.5px] font-extrabold text-[var(--mt-ink)]">{vegetationLabel(ndvi)}</span>
            </div>
            <div className="flex flex-1 flex-col gap-1 rounded-[10px] bg-[var(--mt-sky-tint)] px-2 py-2">
              <span className="flex items-center gap-1 text-[10px] font-extrabold text-[var(--mt-sky-text)]">
                <Droplets className="h-3 w-3" strokeWidth={2.4} />
                Water
              </span>
              <span className="text-[11.5px] font-extrabold text-[var(--mt-ink)]">{moistureLabel(moisture)}</span>
            </div>
            <div className="flex flex-1 flex-col gap-1 rounded-[10px] bg-[var(--mt-gold-tint)] px-2 py-2">
              <span className="flex items-center gap-1 text-[10px] font-extrabold text-[var(--mt-gold-text)]">
                <Wheat className="h-3 w-3" strokeWidth={2.4} />
                Crop
              </span>
              <span className="truncate text-[11.5px] font-extrabold text-[var(--mt-ink)]">{cropLabel}</span>
            </div>
          </div>

          <span className="mt-3 flex h-11 w-full items-center justify-center gap-1.5 rounded-full border-[1.5px] border-[var(--mt-leaf)]/25 text-[13.5px] font-bold text-[var(--mt-leaf-deep)]">
            View Farm
            <ChevronRight className="h-4 w-4" strokeWidth={2.5} />
          </span>
        </div>
      </div>
    </Link>
  );
}
