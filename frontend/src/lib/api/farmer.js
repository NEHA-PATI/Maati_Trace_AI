import {
  farmRegistryClient,
  profileClient,
} from "@/shared/api/serviceClients";

// Dashboard reads are safe to reuse briefly. This avoids refetching the same
// profile/summary/farm data whenever a protected route remounts during normal
// navigation, while still keeping the dashboard reasonably fresh.
const DASHBOARD_CACHE_TTL_MS = 30_000;
const readCache = new Map();

function cachedRead(key, read) {
  const now = Date.now();
  const cached = readCache.get(key);
  if (cached && cached.expiresAt > now) return cached.value;

  const value = Promise.resolve().then(read);
  readCache.set(key, { value, expiresAt: now + DASHBOARD_CACHE_TTL_MS, settled: false });
  value.then(() => {
    const entry = readCache.get(key);
    if (entry?.value === value) entry.settled = true;
  });
  value.catch(() => {
    if (readCache.get(key)?.value === value) readCache.delete(key);
  });
  return value;
}

export function hasCachedFarmerProfile() {
  const entry = readCache.get("profile:me");
  return Boolean(entry?.settled && entry.expiresAt > Date.now());
}

export function invalidateFarmerDashboardCache() {
  readCache.clear();
}

function unwrapFarmerProfile(payload) {
  if (
    payload?.profile_type === "farmer"
    && payload?.profile
  ) {
    return {
      ...payload.profile,
      onboarding_status:
        payload.onboarding_status,
      completion_percentage:
        payload.completion_percentage,
      missing_fields:
        payload.missing_fields || [],
    };
  }

  if (payload?.farmer_id) {
    return payload;
  }

  throw new Error(
    "A farmer profile is not available for this account.",
  );
}

export async function getMyFarmerProfile() {
  const payload = await cachedRead("profile:me", () => profileClient.request("/v1/profiles/me"));

  return unwrapFarmerProfile(payload);
}

export async function getFarmer(farmerId) {
  const payload = await cachedRead(`profile:${farmerId}`, () => profileClient.request(`/v1/profiles/farmers/${farmerId}`));

  return unwrapFarmerProfile(payload);
}

export const getFarmerSummary =
  (farmerId) =>
    cachedRead(`summary:${farmerId}`, () => farmRegistryClient.request(`/v1/farmers/${farmerId}/summary`));

export const getFarmerFarms =
  (farmerId) =>
    cachedRead(`farms:${farmerId}`, () => farmRegistryClient.request(`/v1/farmers/${farmerId}/farms`));

export const uploadFarmerDocument =
  async (
    file,
    documentType,
  ) => {
    void file;
    void documentType;

    return {
      status: "backend_pending",
      message:
        "Document upload backend pending",
    };
  };
