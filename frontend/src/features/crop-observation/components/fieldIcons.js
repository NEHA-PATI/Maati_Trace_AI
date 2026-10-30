import {
  AlertTriangle,
  Archive,
  Bug,
  Camera,
  Check,
  CircleHelp,
  Droplets,
  FlaskConical,
  Hand,
  Leaf,
  MapPin,
  Package,
  Scissors,
  Shield,
  Shovel,
  Sprout,
  Sun,
  Trees,
  Waves,
  Wheat,
} from "lucide-react";

export const PRACTICE_ICONS = {
  nutrient_management: FlaskConical,
  weed_management: Sprout,
  pest_management: Bug,
  disease_management: Leaf,
  harvest_management: Wheat,
  post_harvest: Package,
  seed_management: Sprout,
  nursery_management: Shovel,
  orchard_management: Trees,
  crop_damage: AlertTriangle,
};

export const FIELD_ICONS = {
  input_category: FlaskConical,
  product_code: Package,
  quantity: Droplets,
  application_method: Hand,
  application_area: MapPin,
  pest_observed: Bug,
  disease_observed: Leaf,
  severity: AlertTriangle,
  control_method: Shield,
  damage_cause: AlertTriangle,
  harvest_method: Scissors,
  quantity_harvested: Wheat,
  harvest_area: MapPin,
  drying_method: Sun,
  storage_method: Archive,
  orchard_condition: Trees,
  seed_source: Sprout,
  nursery_condition: Shovel,
  weed_method: Sprout,
};

export const OPTION_ICONS = {
  CHEMICAL_FERTILIZER: FlaskConical,
  ORGANIC: Leaf,
  MICRONUTRIENT: Droplets,
  UREA: FlaskConical,
  DAP: Package,
  NPK: Package,
  BROADCAST: Hand,
  SOIL: Shovel,
  FOLIAR: Leaf,
  WHOLE_FARM: Sprout,
  SELECTED_AREA: MapPin,
  SMALL_PART: MapPin,
  ABOUT_HALF: MapPin,
  MOST_OF_FARM: MapPin,
  MANUAL: Hand,
  MECHANICAL: Shovel,
  HERBICIDE: FlaskConical,
  GOOD: Check,
  AVERAGE: CircleHelp,
  POOR: AlertTriangle,
  OWN_SAVED: Sprout,
  MARKET_PURCHASED: Package,
  GOVT_SUPPLIED: Shield,
  STEM_BORER: Bug,
  BROWN_PLANTHOPPER: Bug,
  LEAF_FOLDER: Leaf,
  BLAST: AlertTriangle,
  BLIGHT: Leaf,
  SHEATH_BLIGHT: Leaf,
  NOT_SURE: CircleHelp,
  CARBOFURAN: FlaskConical,
  IMIDACLOPRID: FlaskConical,
  COPPER_FUNGICIDE: FlaskConical,
  OTHER: CircleHelp,
};

export const OPTION_ICON_COLORS = {
  CHEMICAL_FERTILIZER: "text-amber-600",
  ORGANIC: "text-emerald-600",
  MICRONUTRIENT: "text-sky-600",
  UREA: "text-violet-600",
  DAP: "text-indigo-600",
  NPK: "text-teal-600",
  BROADCAST: "text-indigo-600",
  SOIL: "text-amber-700",
  FOLIAR: "text-emerald-600",
  WHOLE_FARM: "text-emerald-700",
  SELECTED_AREA: "text-violet-600",
  SMALL_PART: "text-sky-600",
  ABOUT_HALF: "text-amber-600",
  MOST_OF_FARM: "text-orange-600",
  MANUAL: "text-slate-600",
  MECHANICAL: "text-blue-600",
  HERBICIDE: "text-lime-700",
  GOOD: "text-emerald-600",
  AVERAGE: "text-amber-600",
  POOR: "text-rose-600",
  OWN_SAVED: "text-emerald-600",
  MARKET_PURCHASED: "text-blue-600",
  GOVT_SUPPLIED: "text-indigo-600",
  STEM_BORER: "text-orange-600",
  BROWN_PLANTHOPPER: "text-amber-700",
  LEAF_FOLDER: "text-emerald-600",
  BLAST: "text-rose-600",
  BLIGHT: "text-orange-600",
  SHEATH_BLIGHT: "text-amber-600",
  NOT_SURE: "text-slate-500",
  CARBOFURAN: "text-orange-600",
  IMIDACLOPRID: "text-rose-600",
  COPPER_FUNGICIDE: "text-cyan-700",
  OTHER: "text-slate-500",
};

export function iconForPractice(code) {
  return PRACTICE_ICONS[code] || Leaf;
}

export function iconForField(field) {
  return FIELD_ICONS[field?.field_code] || CircleHelp;
}

export function iconForOption(optionCode, field) {
  return OPTION_ICONS[optionCode] || iconForField(field);
}

export function colorForOption(optionCode) {
  return OPTION_ICON_COLORS[optionCode] || "text-[#5B6055]";
}

export function colorForField(fieldCode) {
  return {
    input_category: "text-emerald-700",
    product_code: "text-indigo-600",
    quantity: "text-violet-600",
    application_method: "text-blue-600",
    application_area: "text-rose-600",
    pest_observed: "text-orange-600",
    disease_observed: "text-emerald-600",
    severity: "text-amber-600",
    control_method: "text-cyan-700",
  }[fieldCode] || "text-[#33492A]";
}

export const MediaCameraIcon = Camera;
export const VoiceWaveIcon = Waves;
