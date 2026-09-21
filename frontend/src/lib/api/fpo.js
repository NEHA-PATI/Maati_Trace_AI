import {
  farmRegistryClient,
  fpoManagementClient,
  profileClient,
} from "@/shared/api/serviceClients";

function unwrapFpoProfile(payload) {
  if (
    payload?.profile_type === "fpo"
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

  if (payload?.fpo_id) {
    return payload;
  }

  throw new Error(
    "An FPO profile is not available for this account.",
  );
}

export async function getMyFpo() {
  const payload =
    await profileClient.request(
      "/v1/profiles/me",
    );

  return unwrapFpoProfile(payload);
}

export function getFpoBootstrapStatus() {
  return fpoManagementClient.request(
    "/v1/fpo-portal/bootstrap-status",
  );
}

export function getFpoVerificationStatus() {
  return fpoManagementClient.request(
    "/v1/fpo-portal/verification",
  );
}

export function submitFpoVerification() {
  return fpoManagementClient.request(
    "/v1/fpo-portal/verification/submit",
    { method: "POST", body: {} },
  );
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

export async function getFpo(fpoId) {
  const payload =
    await profileClient.request(
      `/v1/profiles/fpos/${fpoId}`,
    );

  return unwrapFpoProfile(payload);
}

export const getFpos =
  () => profileClient.request("/v1/profiles/fpos");

export const getFpoSummary =
  (fpoId) =>
    farmRegistryClient.request(
      `/v1/fpos/${fpoId}/summary`,
    );

export const getFpoFarmers =
  (fpoId) =>
    profileClient.request(
      `/v1/profiles/fpos/${fpoId}/farmers`,
    );

export const getFpoFarms =
  (fpoId) =>
    farmRegistryClient.request(
      `/v1/fpos/${fpoId}/farms`,
    );
