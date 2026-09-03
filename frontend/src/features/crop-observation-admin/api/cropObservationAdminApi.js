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
