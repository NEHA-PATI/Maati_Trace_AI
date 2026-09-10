import { analyticsClient, observabilityClient } from "@/shared/api/serviceClients";

const items = (value) => (Array.isArray(value) ? value : value?.items || []);

/* ---------------- Observability (admin monitoring) ---------------- */

export async function getFeatureProcessingSummary() {
  return observabilityClient.request(`/v1/observability/feature-processing/summary`);
}
export async function getFeatureProcessingRuns(limit = 100) {
  return items(await observabilityClient.request(`/v1/observability/feature-processing/runs?limit=${limit}`));
}
export async function getFeatureProcessingSources() {
  return items(await observabilityClient.request(`/v1/observability/feature-processing/sources`));
}
export async function getFeatureProcessingFormulaStatus() {
  return observabilityClient.request(`/v1/observability/feature-processing/formulas`);
}
export async function getFeatureFarmStatus(farmId) {
  return observabilityClient.request(`/v1/observability/feature-processing/farms/${farmId}`);
}

/* ---------------- Admin crop-profile configuration ---------------- */

export async function getAdminCropProfiles() {
  return items(await analyticsClient.request(`/v1/analytics/admin/crop-profiles?include_inactive=true`));
}
export async function createCropProfile(payload) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles`, { method: "POST", body: payload });
}
export async function updateCropProfile(profileId, payload) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles/${profileId}`, { method: "PUT", body: payload });
}
export async function publishCropProfile(profileId) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles/${profileId}/publish`, { method: "POST", body: {} });
}
export async function cloneCropProfile(profileId, newVersion) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles/${profileId}/clone`, {
    method: "POST",
    body: { new_version: newVersion },
  });
}
export async function seedFormulasIntoProfile(profileId, payload) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles/${profileId}/seed-formulas`, {
    method: "POST",
    body: payload,
  });
}
export async function publishAllFormulasForProfile(profileId) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles/${profileId}/publish-formulas`, {
    method: "POST",
    body: {},
  });
}
export async function deleteCropProfile(profileId) {
  return analyticsClient.request(`/v1/analytics/admin/crop-profiles/${profileId}`, { method: "DELETE" });
}
export async function deleteFormula(formulaId) {
  return analyticsClient.request(`/v1/analytics/admin/formulas/${formulaId}`, { method: "DELETE" });
}

/* ---------------- Admin formula-registry configuration ---------------- */

export async function getAdminFormulas(cropCode = "") {
  const query = cropCode ? `&crop_code=${encodeURIComponent(cropCode)}` : "";
  return items(await analyticsClient.request(`/v1/analytics/admin/formulas?include_inactive=true${query}`));
}
export async function createFormula(payload) {
  return analyticsClient.request(`/v1/analytics/admin/formulas`, { method: "POST", body: payload });
}
export async function updateFormula(formulaId, payload) {
  return analyticsClient.request(`/v1/analytics/admin/formulas/${formulaId}`, { method: "PUT", body: payload });
}
export async function publishFormula(formulaId) {
  return analyticsClient.request(`/v1/analytics/admin/formulas/${formulaId}/publish`, { method: "POST", body: {} });
}
export async function cloneFormula(formulaId, newVersion) {
  return analyticsClient.request(`/v1/analytics/admin/formulas/${formulaId}/clone`, {
    method: "POST",
    body: { new_version: newVersion },
  });
}
export async function cloneCropConfiguration(payload) {
  return analyticsClient.request(`/v1/analytics/admin/crops/clone`, { method: "POST", body: payload });
}
export async function getComponentCatalog() {
  return items(await analyticsClient.request(`/v1/analytics/components`));
}
