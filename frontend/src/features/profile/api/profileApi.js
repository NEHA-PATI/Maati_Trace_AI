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

  getFpoStructuredProfile() {
    return profileClient.request("/v1/fpo/me/profile/structured");
  },

  getFpoReadiness() {
    return profileClient.request("/v1/fpo/me/profile/readiness");
  },

  addFpoCommodity(payload) {
    return profileClient.request("/v1/fpo/me/profile/commodities", { method: "POST", body: payload });
  },

  removeFpoCommodity(code) {
    return profileClient.request(`/v1/fpo/me/profile/commodities/${encodeURIComponent(code)}`, { method: "DELETE" });
  },

  addFpoService(payload) {
    return profileClient.request("/v1/fpo/me/profile/services", { method: "POST", body: payload });
  },

  removeFpoService(code) {
    return profileClient.request(`/v1/fpo/me/profile/services/${encodeURIComponent(code)}`, { method: "DELETE" });
  },

  addFpoServiceArea(payload) {
    return profileClient.request("/v1/fpo/me/profile/service-areas", { method: "POST", body: payload });
  },

  removeFpoServiceArea(id) {
    return profileClient.request(`/v1/fpo/me/profile/service-areas/${id}`, { method: "DELETE" });
  },

  getAdminFpoProfile(fpoId) {
    return profileClient.request(`/api/admin-profiles/fpo/organizations/${fpoId}/profile`);
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
