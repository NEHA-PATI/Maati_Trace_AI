import { MAP_CONFIG } from "@/lib/mapConfig";

const locationCache = new Map();

function clean(value) { return String(value || "").trim(); }

function buildQuery({ stateName, districtName, blockName, villageName }) {
  return [villageName, blockName, districtName, stateName || "Odisha", "India"]
    .map(clean).filter(Boolean).join(", ");
}

export async function geocodeLocation(location) {
  if (!MAP_CONFIG.apiKey) throw new Error("Map location search is not configured. Use your current location or continue manually.");
  const query = buildQuery(location);
  if (!query) throw new Error("Select a district or enter a village.");
  if (locationCache.has(query)) return locationCache.get(query);

  const params = new URLSearchParams({
    SingleLine: query,
    countryCode: "IND",
    maxLocations: "5",
    outFields: "Match_addr,Addr_type,City,District,Subregion,Region,Country",
    forStorage: "false",
    f: "json",
    token: MAP_CONFIG.apiKey,
  });
  const response = await fetch(`https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?${params}`);
  if (!response.ok) throw new Error("The location service is temporarily unavailable.");
  const payload = await response.json();
  if (payload.error) {
    const message = String(payload.error.message || "");
    if (payload.error.code === 498 || payload.error.code === 499 || /invalid token|token required/i.test(message)) {
      throw new Error("The configured ArcGIS key was rejected. Add a valid ArcGIS API key with Geocoding access, then restart Vite.");
    }
    throw new Error(message || "Location search failed.");
  }
  const candidates = Array.isArray(payload.candidates) ? payload.candidates : [];
  if (!candidates.length) throw new Error("We could not locate this village. Check its spelling or use your current location.");
  const candidate = candidates.find((item) => Number(item.score) >= 80) || candidates[0];
  const result = {
    query,
    latitude: Number(candidate.location.y),
    longitude: Number(candidate.location.x),
    score: Number(candidate.score || 0),
    address: candidate.address,
    attributes: candidate.attributes || {},
    extent: candidate.extent || null,
  };
  locationCache.set(query, result);
  return result;
}

export async function resolveFarmLocation(formData) {
  const attempts = [
    { precision: "village", villageName: formData.village_name, blockName: formData.block_name, districtName: formData.district_name, stateName: formData.state_name },
    { precision: "block", villageName: "", blockName: formData.block_name, districtName: formData.district_name, stateName: formData.state_name },
    { precision: "district", villageName: "", blockName: "", districtName: formData.district_name, stateName: formData.state_name },
  ];
  let lastError;
  for (const attempt of attempts) {
    try { return { ...(await geocodeLocation(attempt)), precision: attempt.precision }; } catch (error) { lastError = error; }
  }
  throw lastError || new Error("Location could not be found.");
}
