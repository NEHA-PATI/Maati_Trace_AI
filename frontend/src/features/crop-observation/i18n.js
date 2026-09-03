/**
 * Central bilingual string table for the crop diary.
 *
 * Every farmer-facing string lives here as an { en, or } pair so screens never
 * inline `locale === "or-IN" ? ... : ...` ternaries. Only the ACTIVE
 * language is ever rendered on screen — see <Bilingual> and <LanguageToggle>
 * — English and Odia never appear together on the same screen.
 */

export const LOCALES = {
  OR: "or-IN",
  EN: "en-IN",
};

export const STRINGS = {
  myCrop: { en: "My Crop", or: "ମୋ ଫସଲ" },
  chooseCrop: { en: "Choose your crop", or: "ଫସଲ ବାଛନ୍ତୁ" },
  noFarm: {
    en: "You don't have a registered farm yet. Register a farm first to start a crop diary.",
    or: "ଆପଣଙ୍କର କୌଣସି ପଞ୍ଜୀକୃତ ଜମି ନାହିଁ। ପ୍ରଥମେ ଜମି ପଞ୍ଜୀକରଣ କରନ୍ତୁ।",
  },
  active: { en: "Active", or: "ଚାଲୁ ଅଛି" },
  back: { en: "Back", or: "ପଛକୁ" },
  history: { en: "Previous Updates", or: "ପୂର୍ବ ତଥ୍ୟ" },
  today: { en: "Today", or: "ଆଜି" },
  howIsCrop: { en: "How is your crop?", or: "ଫସଲ କେମିତି ଅଛି?" },
  todaysActivities: { en: "Today's farming activities", or: "ଆଜିର କାର୍ଯ୍ୟକଳାପ" },
  loggedToday: { en: "Logged today", or: "ଆଜି ଦିଆଯାଇଛି" },
  saved: { en: "Saved", or: "ସେଭ ହୋଇଛି" },
  saving: { en: "Saving…", or: "ସେଭ ହେଉଛି…" },
  save: { en: "SAVE", or: "ସେଭ କରନ୍ତୁ" },
  loadMore: { en: "Load more", or: "ଆଉ ଦେଖନ୍ତୁ" },
  noUpdates: { en: "No updates recorded yet.", or: "ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ତଥ୍ୟ ନାହିଁ।" },
  couldNotSave: {
    en: "Could not save right now. Your update is safe on this phone.",
    or: "ଏବେ ସେଭ ହେଲା ନାହିଁ। ଆପଣଙ୍କ ତଥ୍ୟ ଏହି ଫୋନରେ ସୁରକ୍ଷିତ ଅଛି।",
  },
  wholeFarm: { en: "Whole Farm", or: "ସମ୍ପୂର୍ଣ୍ଣ ଜମି" },
  selectedArea: { en: "Selected Area", or: "ନିର୍ଦ୍ଦିଷ୍ଟ ଅଂଶ" },
  howMuchFarm: { en: "How much of the farm?", or: "ଜମିର କେତେ ଅଂଶ?" },
  applicationArea: { en: "Where did you apply it?", or: "ପ୍ରୟୋଗ କେଉଁଠି କରିଥିଲେ?" },
  unit: { en: "Unit", or: "ଏକକ" },

  addPhoto: { en: "Add Photo", or: "ଫଟୋ ଯୋଡନ୍ତୁ" },
  recordVoice: { en: "Record Voice", or: "ଭଏସ୍ ରେକର୍ଡ" },
  stopRecording: { en: "Stop", or: "ବନ୍ଦ କରନ୍ତୁ" },
  delete: { en: "Delete", or: "ହଟାନ୍ତୁ" },
  replay: { en: "Replay", or: "ପୁଣି ଶୁଣନ୍ତୁ" },
  listen: { en: "Listen", or: "ଶୁଣନ୍ତୁ" },
  audioUnavailable: { en: "Audio unavailable", or: "ଅଡିଓ ଉପଲବ୍ଧ ନାହିଁ" },
  previousEntries: { en: "Previous entries", or: "ପୂର୍ବ ତଥ୍ୟ" },
  newUpdate: { en: "New Update", or: "ନୂଆ ତଥ୍ୟ" },
  noPreviousEntries: { en: "No previous entries", or: "ପୂର୍ବ ତଥ୍ୟ ନାହିଁ" },
  uploadingMedia: { en: "Saving photo/voice…", or: "ଫଟୋ/ଭଏସ୍ ସେଭ ହେଉଛି…" },
};

export const STATUS_STRINGS = {
  GOOD: { en: "Good", or: "ଭଲ ଅଛି" },
  SOME_PROBLEM: { en: "Some problem", or: "କିଛି ସମସ୍ୟା ଅଛି" },
  SERIOUS_PROBLEM: { en: "Serious problem", or: "ଗୁରୁତର ସମସ୍ୟା ଅଛି" },
};

export const RELATIVE_EXTENT_STRINGS = {
  SMALL_PART: { en: "Small part", or: "ଅଳ୍ପ ଅଂଶ" },
  ABOUT_HALF: { en: "About half", or: "ପ୍ରାୟ ଅଧା" },
  MOST_OF_FARM: { en: "Most of farm", or: "ଅଧିକାଂଶ ଜମି" },
};

export const PRACTICE_META = {
  nutrient_management: { icon: "🌿", en: "Nutrient" },
  weed_management: { icon: "🌱", en: "Weed" },
  pest_management: { icon: "🐛", en: "Pest" },
  disease_management: { icon: "🍂", en: "Disease" },
  harvest_management: { icon: "🌾", en: "Harvest" },
  post_harvest: { icon: "📦", en: "Post-harvest" },
  seed_management: { icon: "🌰", en: "Seed" },
  nursery_management: { icon: "🪴", en: "Nursery" },
  orchard_management: { icon: "🌳", en: "Orchard" },
  crop_damage: { icon: "⚠️", en: "Crop damage" },
};

const isOdia = (locale) => locale === LOCALES.OR;

/** Primary label for the active locale, falling back to whatever exists. */
export function primary(pair, locale) {
  if (!pair) return "";
  return (isOdia(locale) ? pair.or : pair.en) || pair.en || pair.or || "";
}

/** Secondary (support) label — the OTHER language, only when it adds information. */
export function secondary(pair, locale) {
  if (!pair) return "";
  const other = isOdia(locale) ? pair.en : pair.or;
  return other && other !== primary(pair, locale) ? other : "";
}

/** Convenience: look up a STRINGS key and return its primary label. */
export function t(key, locale) {
  return primary(STRINGS[key], locale);
}

export function humanizeCode(code) {
  return String(code || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
