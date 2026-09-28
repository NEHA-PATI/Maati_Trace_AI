import {
  farmRegistryClient,
  fpoManagementClient,
  profileClient,
} from "@/shared/api/serviceClients";

function unwrapFpoProfile(payload) {
  if (payload?.profile_type === "fpo" && payload?.profile) {
    return {
      ...payload.profile,
      onboarding_status: payload.onboarding_status,
      completion_percentage: payload.completion_percentage,
      missing_fields: payload.missing_fields || [],
    };
  }

  if (payload?.fpo_id) {
    return payload;
  }

  throw new Error("An FPO profile is not available for this account.");
}

export async function getMyFpo() {
  const payload = await profileClient.request("/v1/profiles/me");

  return unwrapFpoProfile(payload);
}

export function getFpoBootstrapStatus() {
  return fpoManagementClient.request("/v1/fpo-portal/bootstrap-status");
}

export function getFpoVerificationStatus() {
  return fpoManagementClient.request("/v1/fpo-portal/verification");
}

export function submitFpoVerification() {
  return fpoManagementClient.request("/v1/fpo-portal/verification/submit", {
    method: "POST",
    body: {},
  });
}

export function getFpoVerificationQueue(status = "") {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/verification-queue${query}`,
  );
}

export function reviewFpoVerification(fpoId, status, note = "") {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/organizations/${fpoId}/verification`,
    { method: "PATCH", body: { status, note } },
  );
}

export function getFpoAdminDocuments(fpoId) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/organizations/${fpoId}/verification/documents`,
  );
}

export function getFpoAdminDocumentContent(documentId) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/verification/documents/${documentId}/content`,
    { responseType: "blob" },
  );
}

export function getFpoAdminChecklist(fpoId) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/organizations/${fpoId}/verification/checklist`,
  );
}

export function updateFpoAdminChecklist(resultId, result, note = "") {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/verification/checklist/${resultId}`,
    { method: "PATCH", body: { result, note } },
  );
}

export function validateFpoDocument(documentId, validationStatus, reason = "") {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/verification/documents/${documentId}`,
    { method: "PATCH", body: { validation_status: validationStatus, reason } },
  );
}

export function discoverFpos(query = "") {
  const suffix = query ? `?query=${encodeURIComponent(query)}` : "";
  return fpoManagementClient.request(`/v1/fpo-portal/discover${suffix}`);
}

export function getFpoRelationshipConsentPolicy() {
  return fpoManagementClient.request("/v1/farmer/fpo-consent-policy");
}

export function getFarmerFpoRelationships() {
  return fpoManagementClient.request("/v1/farmer/fpo-relationships");
}

export function getFarmerImportedOnboarding() {
  return fpoManagementClient.request("/v1/farmer/me/imported-onboarding");
}

export function getFarmerImportedOnboardingRecord(stagedRecordId) {
  return fpoManagementClient.request(
    `/v1/farmer/me/imported-onboarding/${stagedRecordId}`,
  );
}

export function linkFarmerImportedFarm(stagedRecordId, farmId) {
  return fpoManagementClient.request(
    `/v1/farmer/me/imported-onboarding/${stagedRecordId}/link-farm`,
    { method: "POST", body: { farm_id: farmId } },
  );
}

export function requestFarmerFpoRelationship(farmId, fpoId, consent = {}) {
  return fpoManagementClient.request("/v1/farmer/farm-relationships", {
    method: "POST",
    body: {
      farm_id: farmId,
      fpo_id: fpoId,
      policy_code: consent.policy_code,
      policy_version: consent.policy_version,
      accepted: consent.accepted === true,
      selected_optional_scopes: consent.selected_optional_scopes || [],
    },
  });
}

export function getFpoRelationships() {
  return fpoManagementClient.request("/v1/fpo-portal/farm-relationships");
}

export function decideFpoRelationship(relationshipId, decision, note = "") {
  return fpoManagementClient.request(
    `/v1/fpo-portal/farm-relationships/${relationshipId}`,
    {
      method: "PATCH",
      body: { decision, note },
    },
  );
}

export function cancelFarmerFpoRelationship(relationshipId) {
  return fpoManagementClient.request(
    `/v1/farmers/me/fpo-relationship-requests/${relationshipId}/cancel`,
    { method: "POST" },
  );
}

export function revokeFarmerFpoRelationship(farmId, relationshipId) {
  return fpoManagementClient.request(
    `/v1/farmer/farms/${farmId}/fpo-relationships/${relationshipId}`,
    {
      method: "DELETE",
    },
  );
}

export function createFpoSupportTicket(payload) {
  return fpoManagementClient.request("/v1/farmer/fpo-support-tickets", {
    method: "POST",
    body: payload,
  });
}

export function getFpoSupportTickets() {
  return fpoManagementClient.request("/v1/farmer/fpo-support-tickets");
}

export function getFpoEntitlements() {
  return fpoManagementClient.request("/v1/fpo-portal/entitlements");
}

export function getFpoPortfolioReport() {
  return fpoManagementClient.request("/v1/fpo-portal/reports/portfolio");
}

export function getFpoOperationalAlerts(status = "") {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return fpoManagementClient.request(`/v1/fpo-portal/alerts${query}`);
}

export function acknowledgeFpoAlert(alertId) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/alerts/${alertId}/acknowledge`,
    {
      method: "PATCH",
      body: {},
    },
  );
}

export function getFpoFeatureCatalogue() {
  return fpoManagementClient.request("/v1/fpo-portal/admin/features/catalogue");
}

export function assignFpoClass(fpoId, classCode) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/organizations/${fpoId}/class`,
    {
      method: "PATCH",
      body: { class_code: classCode },
    },
  );
}

export function createFpoFeatureOverride(fpoId, payload) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/organizations/${fpoId}/feature-overrides`,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function getFpoFeatureOverrides(fpoId) {
  return fpoManagementClient.request(
    `/v1/fpo-portal/admin/organizations/${fpoId}/feature-overrides`,
  );
}

export function runFpoReconciliation() {
  return fpoManagementClient.request(
    "/v1/fpo-portal/admin/reconciliation/run",
    {
      method: "POST",
      body: {},
    },
  );
}

export function getFpoAdminAdvisoryTemplates() {
  return fpoManagementClient.request(
    "/v1/admin/fpo/class-b/advisory-templates",
  );
}

export function createFpoAdminAdvisoryTemplate(body) {
  return fpoManagementClient.request(
    "/v1/admin/fpo/class-b/advisory-templates",
    { method: "POST", body },
  );
}

export function reviewFpoAdminAdvisoryTemplate(templateId, decision) {
  return fpoManagementClient.request(
    `/v1/admin/fpo/class-b/advisory-templates/${templateId}`,
    { method: "PATCH", body: { decision } },
  );
}

export function getFpoClassBReleaseReadiness() {
  return fpoManagementClient.request("/v1/admin/fpo/class-b/release-readiness");
}

export function publishFpoClassBPlan(reason) {
  return fpoManagementClient.request("/v1/admin/fpo/class-b/publish", {
    method: "POST",
    body: { reason },
  });
}

export function getFpoClassCReleaseReadiness() {
  return fpoManagementClient.request("/v1/admin/fpo/class-c/release-readiness");
}

export function publishFpoClassCPlan(reason) {
  return fpoManagementClient.request("/v1/admin/fpo/class-c/publish", {
    method: "POST",
    body: { reason },
  });
}

export async function getFpo(fpoId) {
  const payload = await profileClient.request(`/v1/profiles/fpos/${fpoId}`);

  return unwrapFpoProfile(payload);
}

export const getFpos = () => profileClient.request("/v1/profiles/fpos");

export const getFpoSummary = (fpoId) =>
  farmRegistryClient.request(`/v1/fpos/${fpoId}/summary`);

export const getFpoFarmers = (fpoId) =>
  profileClient.request(`/v1/profiles/fpos/${fpoId}/farmers`);

export const getFpoFarms = (fpoId) =>
  farmRegistryClient.request(`/v1/fpos/${fpoId}/farms`);
