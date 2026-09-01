import { cropObservationClient } from "@/shared/api/serviceClients";
import { cacheInvalidate, cachedRequest } from "@/features/crop-observation/cache";

const BASE = "/v1/crop-observations";

export function getCrops(locale) {
  const query = locale ? `?locale=${encodeURIComponent(locale)}` : "";
  // Catalogue is near-static within a session (server sends max-age=300) — serve
  // from memory so re-entering "My Crop" paints instantly.
  return cachedRequest(
    `crops:${locale || "default"}`,
    () => cropObservationClient.request(`${BASE}/crops${query}`),
    300_000,
  );
}

export function getFarmCrops(farmId) {
  return cachedRequest(
    `farmCrops:${farmId}`,
    () => cropObservationClient.request(`${BASE}/farms/${farmId}/crops`),
    60_000,
  );
}

export function attachCropToFarm(farmId, payload) {
  return cropObservationClient
    .request(`${BASE}/farms/${farmId}/crops`, { method: "POST", body: payload })
    .then((res) => {
      cacheInvalidate(`farmCrops:${farmId}`);
      return res;
    });
}

export function startCropCycle(farmCropId, payload = {}) {
  return cropObservationClient.request(`${BASE}/farm-crops/${farmCropId}/cycles`, {
    method: "POST",
    body: payload,
  });
}

export function getStageScreen(cropCycleId, stageCode, locale) {
  const query = locale ? `?locale=${encodeURIComponent(locale)}` : "";
  return cropObservationClient.request(
    `${BASE}/crop-cycles/${cropCycleId}/stages/${stageCode}/screen${query}`,
  );
}

export function saveDailyStatus(cropCycleId, stageCode, payload) {
  return cropObservationClient.request(
    `${BASE}/crop-cycles/${cropCycleId}/stages/${stageCode}/today`,
    { method: "PUT", body: payload },
  );
}

export function savePracticeObservation(cropCycleId, stageCode, practiceCode, payload) {
  return cropObservationClient
    .request(
      `${BASE}/crop-cycles/${cropCycleId}/stages/${stageCode}/practices/${practiceCode}/today`,
      { method: "PUT", body: payload },
    )
    .then((res) => {
      cacheInvalidate(`screen:${cropCycleId}:`);
      return res;
    });
}

export function getHistory(cropCycleId, { before, limit } = {}) {
  const search = new URLSearchParams();
  if (before) search.set("before", before);
  if (limit) search.set("limit", String(limit));
  const query = search.toString();
  return cropObservationClient.request(
    `${BASE}/crop-cycles/${cropCycleId}/history${query ? `?${query}` : ""}`,
  );
}

export function requestMediaUpload(payload) {
  return cropObservationClient.request(`${BASE}/media/uploads`, {
    method: "POST",
    body: payload,
  });
}

export function completeMediaUpload(mediaAssetId) {
  return cropObservationClient.request(`${BASE}/media/${mediaAssetId}/complete`, {
    method: "POST",
  });
}
