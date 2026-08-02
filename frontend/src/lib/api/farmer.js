import {
  farmRegistryClient,
  profileClient,
} from "@/shared/api/serviceClients";

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
  const payload =
    await profileClient.request(
      "/v1/profiles/me",
    );

  return unwrapFarmerProfile(payload);
}

export async function getFarmer(farmerId) {
  const payload =
    await profileClient.request(
      `/v1/profiles/farmers/${farmerId}`,
    );

  return unwrapFarmerProfile(payload);
}

export const getFarmerSummary =
  (farmerId) =>
    farmRegistryClient.request(
      `/v1/farmers/${farmerId}/summary`,
    );

export const getFarmerFarms =
  (farmerId) =>
    farmRegistryClient.request(
      `/v1/farmers/${farmerId}/farms`,
    );

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
