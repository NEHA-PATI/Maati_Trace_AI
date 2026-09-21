import { getAccessToken } from "@/features/auth/session";
import { cropObservationClient } from "@/shared/api/serviceClients";
import { serviceBaseUrl, servicePath } from "@/shared/api/serviceUrls";
import { cacheInvalidate, cachedRequest } from "@/features/crop-observation/cache";

const BASE = "/v1/crop-observations";

/**
 * Absolute URL for a system-media path (crop card / stage images —
 * unauthenticated, same as GET /crops) so it can be used directly as an
 * <img>/<audio> `src` with no extra fetch.
 */
export function systemMediaUrl(path) {
  if (!path) return null;
  return `${serviceBaseUrl()}${servicePath(path)}`;
}

/**
 * Farmer media (photos / voice notes) needs the Authorization header, which
 * plain <img>/<audio> tags cannot send — so callers fetch the bytes once
 * (on tap, never preloaded — see PreviousEntryRow) and get back a blob URL.
 */
export async function fetchAuthedMediaBlob(path) {
  const token = getAccessToken();
  const accessPath = path.endsWith("/content")
    ? path.replace(/\/content$/, "/access")
    : path;
  const accessResponse = await fetch(`${serviceBaseUrl()}${servicePath(accessPath)}`, {
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!accessResponse.ok) throw new Error("Could not authorize this media.");
  const access = await accessResponse.json();
  const external = Boolean(access.external) || /^https?:\/\//i.test(access.url);
  const targetUrl = external
    ? access.url
    : `${serviceBaseUrl()}${servicePath(access.url)}`;
  const response = await fetch(targetUrl, {
    credentials: external ? "omit" : "include",
    headers: !external && token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error("Could not load this media.");
  return response.blob();
}

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

export function getPracticeHistory(cropCycleId, stageCode, practiceCode, locale, { limit = 20 } = {}) {
  const search = new URLSearchParams();
  if (locale) search.set("locale", locale);
  if (limit) search.set("limit", String(limit));
  return cropObservationClient.request(
    `${BASE}/crop-cycles/${cropCycleId}/stages/${stageCode}/practices/${practiceCode}/history?${search.toString()}`,
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

export function listOwnerMedia(ownerType, ownerId) {
  const search = new URLSearchParams({ owner_type: ownerType, owner_id: ownerId });
  return cropObservationClient.request(`${BASE}/media?${search.toString()}`);
}

export function deleteMedia(mediaAssetId) {
  return cropObservationClient.request(`${BASE}/media/${mediaAssetId}`, { method: "DELETE" });
}

/**
 * Full three-step upload: request an upload slot, PUT the raw bytes to it
 * (works unchanged whether the backend hands back a local-content URL or a
 * real S3 presigned URL), then mark it complete. Mirrors
 * save-observation-first-then-upload-media (see PracticeSheet.jsx) —
 * ownerId must already exist before this is called.
 */
export async function uploadMedia({
  ownerType,
  ownerId,
  mediaType,
  mediaPurpose = "GENERAL",
  mimeType,
  file,
  durationSeconds,
}) {
  const { media_asset_id: mediaAssetId, upload_url: uploadUrl, method, headers } = await requestMediaUpload({
    owner_type: ownerType,
    owner_id: ownerId,
    media_type: mediaType,
    media_purpose: mediaPurpose,
    mime_type: mimeType,
    byte_size: file.size,
    duration_seconds: durationSeconds ?? null,
  });

  const isAbsoluteUpload = /^https?:\/\//i.test(uploadUrl);
  const putUrl = isAbsoluteUpload
    ? uploadUrl
    : `${serviceBaseUrl()}${servicePath(uploadUrl)}`;
  const token = getAccessToken();
  const putResponse = await fetch(putUrl, {
    method: method || "PUT",
    // Never send MaatiTrace cookies/JWT to a presigned S3 URL. The signature
    // in the URL is the temporary upload authorization.
    credentials: isAbsoluteUpload ? "omit" : "include",
    headers: {
      ...(headers || {}),
      ...(!isAbsoluteUpload && token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: file,
  });
  if (!putResponse.ok) throw new Error("Could not upload the file.");

  return completeMediaUpload(mediaAssetId);
}
