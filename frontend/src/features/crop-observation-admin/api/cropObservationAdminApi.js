import { getAccessToken } from "@/features/auth/session";
import { serviceBaseUrl, servicePath } from "@/shared/api/serviceUrls";
import { cropObservationClient } from "@/shared/api/serviceClients";

const BASE = "/v1/crop-observations/admin";

function req(path, options) {
  return cropObservationClient.request(`${BASE}${path}`, options);
}

// Crops
export const listCrops = () => req("/crops");
export const createCrop = (payload) => req("/crops", { method: "POST", body: payload });
export const getCrop = (cropCode) => req(`/crops/${cropCode}`);
export const updateCrop = (cropCode, payload) => req(`/crops/${cropCode}`, { method: "PATCH", body: payload });
export const upsertCropTranslation = (cropCode, locale, payload) =>
  req(`/crops/${cropCode}/translations/${locale}`, { method: "PUT", body: payload });

// Configurations
export const listConfigurations = (cropCode) => req(`/crops/${cropCode}/configurations`);
export const createDraftConfiguration = (cropCode) =>
  req(`/crops/${cropCode}/configurations/draft`, { method: "POST" });
export const cloneConfiguration = (configVersionId) =>
  req(`/configurations/${configVersionId}/clone`, { method: "POST" });
export const validateConfiguration = (configVersionId) =>
  req(`/configurations/${configVersionId}/validate`, { method: "POST" });
export const publishConfiguration = (configVersionId) =>
  req(`/configurations/${configVersionId}/publish`, { method: "POST" });
export const listStages = (configVersionId) => req(`/configurations/${configVersionId}/stages`);
export const reorderStages = (configVersionId, order) =>
  req(`/configurations/${configVersionId}/stage-order`, { method: "PUT", body: { order } });

// Stages
export const createStage = (configVersionId, payload) =>
  req(`/configurations/${configVersionId}/stages`, { method: "POST", body: payload });
export const updateStage = (stageId, payload) => req(`/stages/${stageId}`, { method: "PATCH", body: payload });
export const deleteStage = (stageId) => req(`/stages/${stageId}`, { method: "DELETE" });
export const upsertStageTranslation = (stageId, locale, payload) =>
  req(`/stages/${stageId}/translations/${locale}`, { method: "PUT", body: payload });

// Practices
export const listPracticeTemplates = () => req("/practice-templates");
export const listStagePractices = (stageId) => req(`/stages/${stageId}/practices`);
export const createStagePractice = (stageId, payload) =>
  req(`/stages/${stageId}/practices`, { method: "POST", body: payload });
export const updateStagePractice = (stagePracticeId, payload) =>
  req(`/stage-practices/${stagePracticeId}`, { method: "PATCH", body: payload });
export const deleteStagePractice = (stagePracticeId) =>
  req(`/stage-practices/${stagePracticeId}`, { method: "DELETE" });
export const upsertPracticeTranslation = (practiceTemplateId, locale, payload) =>
  req(`/practices/${practiceTemplateId}/translations/${locale}`, { method: "PUT", body: payload });

// Fields
export const listFields = (stagePracticeId) => req(`/stage-practices/${stagePracticeId}/fields`);
export const createField = (stagePracticeId, payload) =>
  req(`/stage-practices/${stagePracticeId}/fields`, { method: "POST", body: payload });
export const updateField = (fieldId, payload) => req(`/fields/${fieldId}`, { method: "PATCH", body: payload });
export const deleteField = (fieldId) => req(`/fields/${fieldId}`, { method: "DELETE" });
export const upsertFieldTranslation = (fieldId, locale, payload) =>
  req(`/fields/${fieldId}/translations/${locale}`, { method: "PUT", body: payload });

// Options
export const listOptions = (fieldId) => req(`/fields/${fieldId}/options`);
export const createOption = (fieldId, payload) => req(`/fields/${fieldId}/options`, { method: "POST", body: payload });
export const updateOption = (optionId, payload) => req(`/options/${optionId}`, { method: "PATCH", body: payload });
export const deleteOption = (optionId) => req(`/options/${optionId}`, { method: "DELETE" });
export const upsertOptionTranslation = (optionId, locale, payload) =>
  req(`/options/${optionId}/translations/${locale}`, { method: "PUT", body: payload });

// Observation monitor
export const getObservationsSummary = () => req("/observations/summary");
export const listObservations = (params = {}) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const query = search.toString();
  return req(`/observations${query ? `?${query}` : ""}`);
};
export const getObservationDetail = (id) => req(`/observations/${id}`);

// TTS
export const getTtsStatus = () => req("/tts/status");
export const listTtsVoices = (language) => req(`/tts/voices?language=${encodeURIComponent(language)}`);
export const listTtsProfiles = () => req("/tts/profiles");
export const upsertTtsProfile = (locale, payload) =>
  req(`/tts/profiles/${locale}`, { method: "PUT", body: payload });
export const generateStageInstructionAudio = (stageId, locale, payload = {}) =>
  req(`/stages/${stageId}/instruction-audio/${locale}/generate`, { method: "POST", body: payload });

// ---------------------------------------------------------------------------
// Crop Observation master-admin V2
// ---------------------------------------------------------------------------
export const getOverview = (params = {}) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const query = search.toString();
  return req(`/overview${query ? `?${query}` : ""}`);
};

export const listPracticeRecords = (params = {}) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const query = search.toString();
  return req(`/records${query ? `?${query}` : ""}`);
};

export const getPracticeRecord = (recordId) => req(`/records/${recordId}`);
export const updatePracticeRecordReview = (recordId, payload) =>
  req(`/records/${recordId}/review`, { method: "PUT", body: payload });
export const listIssues = (params = {}) => {
  const search = new URLSearchParams(params);
  const query = search.toString();
  return req(`/issues${query ? `?${query}` : ""}`);
};
export const getCropObservationSystemStatus = () => req("/system/status");

export const listSystemMedia = (params = {}) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const query = search.toString();
  return req(`/system-media${query ? `?${query}` : ""}`);
};

export const requestSystemMediaUpload = (payload) =>
  req("/system-media/uploads", { method: "POST", body: payload });

export const completeSystemMediaUpload = (assetId, binding) => {
  const search = new URLSearchParams();
  Object.entries(binding).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  return req(`/system-media/${assetId}/complete?${search.toString()}`, { method: "POST" });
};

export const deleteSystemMediaBinding = (bindingId) =>
  req(`/system-media/bindings/${bindingId}`, { method: "DELETE" });

export const generateConfigurationAudio = (configVersionId, payload = {}) =>
  req(`/configurations/${configVersionId}/generate-audio`, { method: "POST", body: payload });


export async function uploadSystemMedia({ file, targetType, targetId, assetRole, locale = null, durationSeconds = null, slotNumber = null }) {
  const ticket = await requestSystemMediaUpload({
    target_type: targetType,
    target_id: targetId,
    asset_role: assetRole,
    locale,
    mime_type: file.type,
    byte_size: file.size,
    duration_seconds: durationSeconds,
    original_filename: file.name,
    slot_number: slotNumber,
  });

  const isAbsoluteUpload = /^https?:\/\//i.test(ticket.upload_url);
  const uploadUrl = isAbsoluteUpload
    ? ticket.upload_url
    : `${serviceBaseUrl()}${servicePath(ticket.upload_url)}`;
  const token = getAccessToken();
  const uploadResponse = await fetch(uploadUrl, {
    method: ticket.method || "PUT",
    credentials: isAbsoluteUpload ? "omit" : "include",
    headers: {
      ...(ticket.headers || {}),
      ...(!isAbsoluteUpload && token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: file,
  });
  if (!uploadResponse.ok) throw new Error("Could not upload media.");

  return completeSystemMediaUpload(ticket.asset_id, {
    target_type: targetType,
    target_id: targetId,
    asset_role: assetRole,
    locale,
    slot_number: slotNumber,
  });
}


export function resolveCropObservationServiceUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${serviceBaseUrl()}${servicePath(path)}`;
}

export async function fetchAdminMediaBlob(path) {
  const token = getAccessToken();
  if (/^https?:\/\//i.test(path)) {
    const direct = await fetch(path, { credentials: "omit" });
    if (!direct.ok) throw new Error("Could not load media.");
    return direct.blob();
  }

  const accessPath = path.endsWith("/content")
    ? path.replace(/\/content$/, "/access")
    : path;
  const accessResponse = await fetch(`${serviceBaseUrl()}${servicePath(accessPath)}`, {
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!accessResponse.ok) throw new Error("Could not authorize media.");
  const access = await accessResponse.json();
  const external = Boolean(access.external) || /^https?:\/\//i.test(access.url);
  const targetUrl = external
    ? access.url
    : `${serviceBaseUrl()}${servicePath(access.url)}`;
  const response = await fetch(targetUrl, {
    credentials: external ? "omit" : "include",
    headers: !external && token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error("Could not load media.");
  return response.blob();
}
