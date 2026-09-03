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

export function iconForPractice(code) {
  return PRACTICE_ICONS[code] || Leaf;
}

export function iconForField(field) {
  return FIELD_ICONS[field?.field_code] || CircleHelp;
}

export function iconForOption(optionCode, field) {
  return OPTION_ICONS[optionCode] || iconForField(field);
}

export const MediaCameraIcon = Camera;
export const VoiceWaveIcon = Waves;
