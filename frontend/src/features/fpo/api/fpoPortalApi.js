import { fpoManagementClient } from "@/shared/api/serviceClients";

export function getFpoPortalBootstrap() {
  return fpoManagementClient.request("/v1/fpo-portal/bootstrap");
}

export function getFpoPortalEntitlements() {
  return fpoManagementClient.request("/v1/fpo-portal/entitlements");
}

export function getFpoVerification() {
  return fpoManagementClient.request("/v1/fpo-portal/verification");
}

export function submitFpoVerification() {
  return fpoManagementClient.request("/v1/fpo-portal/verification/submit", {
    method: "POST",
    body: {},
  });
}

export function getFpoVerificationDocuments() {
  return fpoManagementClient.request("/v1/fpo/me/documents");
}

export function createFpoDocumentUploadIntent(payload) {
  return fpoManagementClient.request("/v1/fpo/me/documents/upload-intents", {
    method: "POST",
    body: payload,
  });
}

export function uploadFpoVerificationDocument(
  documentId,
  file,
  uploadUrl = "",
) {
  const target = uploadUrl || `/v1/fpo/me/documents/${documentId}/content`;
  if (/^https?:\/\//i.test(target)) {
    return fetch(target, {
      method: "PUT",
      headers: { "Content-Type": file.type },
      body: file,
    }).then(async (response) => {
      if (!response.ok)
        throw new Error("The document could not be uploaded to storage.");
      return response;
    });
  }
  return fpoManagementClient.request(target, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });
}

export function finalizeFpoVerificationDocument(documentId, checksum) {
  return fpoManagementClient.request(
    `/v1/fpo/me/documents/${documentId}/finalize`,
    {
      method: "POST",
      body: { checksum },
    },
  );
}

export function deleteFpoVerificationDocument(documentId) {
  return fpoManagementClient.request(`/v1/fpo/me/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function getFpoImportTemplate(importType) {
  return fpoManagementClient.request(
    `/v1/fpo/me/import-templates/${importType}`,
  );
}

export function createFpoImportIntent(payload) {
  return fpoManagementClient.request("/v1/fpo/me/imports/upload-intents", {
    method: "POST",
    body: payload,
  });
}

export function uploadFpoImportContent(jobId, file) {
  return fpoManagementClient.request(`/v1/fpo/me/imports/${jobId}/content`, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type || "text/csv" },
  });
}

export function validateFpoImport(jobId) {
  return fpoManagementClient.request(`/v1/fpo/me/imports/${jobId}/validate`, {
    method: "POST",
  });
}

export function commitFpoImport(jobId) {
  return fpoManagementClient.request(`/v1/fpo/me/imports/${jobId}/commit`, {
    method: "POST",
  });
}

export function getFpoImports() {
  return fpoManagementClient.request("/v1/fpo/me/imports");
}

export function getFpoImportRows(jobId) {
  return fpoManagementClient.request(`/v1/fpo/me/imports/${jobId}/rows`);
}

export function getFpoStagedImportRecords(jobId) {
  return fpoManagementClient.request(
    `/v1/fpo/me/imports/${jobId}/staged-records`,
  );
}

export function getFarmerImportedOnboarding() {
  return fpoManagementClient.request("/v1/farmer/me/imported-onboarding");
}

export function cancelFpoImport(jobId) {
  return fpoManagementClient.request(`/v1/fpo/me/imports/${jobId}/cancel`, {
    method: "POST",
  });
}

export function getFpoDataQualitySummary() {
  return fpoManagementClient.request("/v1/fpo/me/data-quality/summary");
}

export function getFpoDataQualityIssues() {
  return fpoManagementClient.request("/v1/fpo/me/data-quality/issues");
}

export const getFpoTags = () => fpoManagementClient.request("/v1/fpo/me/tags");
export const createFpoTag = (body) =>
  fpoManagementClient.request("/v1/fpo/me/tags", { method: "POST", body });
export const getFpoSegments = () =>
  fpoManagementClient.request("/v1/fpo/me/segments");
export const createFpoSegment = (body) =>
  fpoManagementClient.request("/v1/fpo/me/segments", { method: "POST", body });
export const evaluateFpoSegment = (id) =>
  fpoManagementClient.request(`/v1/fpo/me/segments/${id}/evaluate`, {
    method: "POST",
  });
export const getFpoSeasonPlans = () =>
  fpoManagementClient.request("/v1/fpo/me/season-plans");
export const createFpoSeasonPlan = (body) =>
  fpoManagementClient.request("/v1/fpo/me/season-plans", {
    method: "POST",
    body,
  });
export const getFpoTasks = () =>
  fpoManagementClient.request("/v1/fpo/me/tasks");
export const createFpoTask = (body) =>
  fpoManagementClient.request("/v1/fpo/me/tasks", { method: "POST", body });
export const updateFpoTask = (id, body) =>
  fpoManagementClient.request(`/v1/fpo/me/tasks/${id}`, {
    method: "PATCH",
    body,
  });
export const getFpoMonitoringSummary = () =>
  fpoManagementClient.request("/v1/fpo/me/monitoring/summary");
export const getFpoAlertMetrics = () =>
  fpoManagementClient.request("/v1/fpo/me/alert-rules/metrics");
export const getFpoAlertRules = () =>
  fpoManagementClient.request("/v1/fpo/me/alert-rules");
export const createFpoAlertRule = (body) =>
  fpoManagementClient.request("/v1/fpo/me/alert-rules", {
    method: "POST",
    body,
  });
export const publishFpoAlertRule = (id) =>
  fpoManagementClient.request(`/v1/fpo/me/alert-rules/${id}/publish`, {
    method: "POST",
  });
export const getFpoAdvisoryTemplates = () =>
  fpoManagementClient.request("/v1/fpo/me/advisory-templates");
export const getFpoCampaigns = () =>
  fpoManagementClient.request("/v1/fpo/me/campaigns");
export const createFpoCampaign = (body) =>
  fpoManagementClient.request("/v1/fpo/me/campaigns", { method: "POST", body });
export const estimateFpoCampaign = (id) =>
  fpoManagementClient.request(`/v1/fpo/me/campaigns/${id}/estimate`, {
    method: "POST",
  });
export const getFpoInputPlans = () =>
  fpoManagementClient.request("/v1/fpo/me/input-demand-plans");
export const getFpoForecasts = () =>
  fpoManagementClient.request("/v1/fpo/me/yield-forecasts");
export const runFpoForecast = (body) =>
  fpoManagementClient.request("/v1/fpo/me/yield-forecasts/run", {
    method: "POST",
    body,
  });
export const getFpoReportCatalogue = () =>
  fpoManagementClient.request("/v1/fpo/me/reports/catalogue");
export const getFpoReportJobs = () =>
  fpoManagementClient.request("/v1/fpo/me/report-jobs");
export const getFpoCounterparties = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/counterparties");
export const createFpoCounterparty = (body) =>
  fpoManagementClient.request("/v1/fpo/me/class-c/counterparties", {
    method: "POST",
    body,
  });
export const reviewFpoCounterparty = (id, body) =>
  fpoManagementClient.request(
    `/v1/fpo/me/class-c/counterparties/${id}/due-diligence`,
    { method: "PATCH", body },
  );
export const getFpoOpportunities = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/opportunities");
export const createFpoOpportunity = (body) =>
  fpoManagementClient.request("/v1/fpo/me/class-c/opportunities", {
    method: "POST",
    body,
  });
export const transitionFpoOpportunity = (id, body) =>
  fpoManagementClient.request(`/v1/fpo/me/class-c/opportunities/${id}/stage`, {
    method: "PATCH",
    body,
  });
export const getFpoProcurementPlans = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/procurement-plans");
export const createFpoProcurementPlan = (body) =>
  fpoManagementClient.request("/v1/fpo/me/class-c/procurement-plans", {
    method: "POST",
    body,
  });
export const getFpoProcurementItems = (id) =>
  fpoManagementClient.request(
    `/v1/fpo/me/class-c/procurement-plans/${id}/items`,
  );
export const addFpoProcurementItem = (id, body) =>
  fpoManagementClient.request(
    `/v1/fpo/me/class-c/procurement-plans/${id}/items`,
    { method: "POST", body },
  );
export const transitionFpoProcurementPlan = (id, body) =>
  fpoManagementClient.request(
    `/v1/fpo/me/class-c/procurement-plans/${id}/status`,
    { method: "PATCH", body },
  );
export const getFpoLots = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/lots");
export const createFpoLot = (body) =>
  fpoManagementClient.request("/v1/fpo/me/class-c/lots", {
    method: "POST",
    body,
  });
export const sealFpoLot = (id) =>
  fpoManagementClient.request(`/v1/fpo/me/class-c/lots/${id}/seal`, {
    method: "POST",
    body: {},
  });
export const getFpoQualityInspections = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/quality/inspections");
export const getFpoInventory = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/inventory");
export const getFpoContracts = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/contracts");
export const getFpoOrders = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/orders");
export const getFpoDispatches = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/dispatches");
export const getFpoComplianceDocuments = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/compliance/documents");
export const getFpoComplianceReadiness = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/compliance/readiness");
export const getFpoExportPacks = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/export-packs");
export const getFpoDataPackSchemas = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/data-packs/schemas");
export const getFpoSustainabilityMetrics = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/sustainability/metrics");
export const getFpoApiClients = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/integrations/api-clients");
export const getFpoWebhooks = () =>
  fpoManagementClient.request("/v1/fpo/me/class-c/integrations/webhooks");
