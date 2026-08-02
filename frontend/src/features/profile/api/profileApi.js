import {
  profileClient,
} from "@/shared/api/serviceClients";

export const profileApi = Object.freeze({
  getMyProfile() {
    return profileClient.request(
      "/v1/profiles/me",
    );
  },

  updateMyFarmerProfile(payload) {
    return profileClient.request(
      "/v1/profiles/farmer/me",
      {
        method: "PATCH",
        body: payload,
      },
    );
  },

  setupMyFpoProfile(payload) {
    return profileClient.request(
      "/v1/profiles/fpo/setup",
      {
        method: "POST",
        body: payload,
      },
    );
  },

  updateMyFpoProfile(payload) {
    return profileClient.request(
      "/v1/profiles/fpo/me",
      {
        method: "PATCH",
        body: payload,
      },
    );
  },

  exportMyProfile() {
    return profileClient.request(
      "/v1/profiles/me/export",
    );
  },

  getFarmerProfile(farmerId) {
    return profileClient.request(
      `/v1/profiles/farmers/${farmerId}`,
    );
  },

  getFpoProfile(fpoId) {
    return profileClient.request(
      `/v1/profiles/fpos/${fpoId}`,
    );
  },

  getFpoFarmers(fpoId) {
    return profileClient.request(
      `/v1/profiles/fpos/${fpoId}/farmers`,
    );
  },
});
