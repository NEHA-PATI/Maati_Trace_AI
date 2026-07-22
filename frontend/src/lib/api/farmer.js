import { farmRegistryClient } from "./client";
export const getMyFarmerProfile = () => farmRegistryClient.request("/v1/farmers/me");
export const getFarmer = (farmerId) => farmRegistryClient.request(`/v1/farmers/${farmerId}`);
export const getFarmerSummary = (farmerId) => farmRegistryClient.request(`/v1/farmers/${farmerId}/summary`);
export const getFarmerFarms = (farmerId) => farmRegistryClient.request(`/v1/farmers/${farmerId}/farms`);
export const createFarmer = (payload) => farmRegistryClient.request("/v1/farmers", { method: "POST", body: JSON.stringify(payload) });
export const updateMyFarmerProfile = (payload) => farmRegistryClient.request("/v1/farmers/me/profile", { method: "PATCH", body: JSON.stringify(payload) });
export const exportMyFarmerProfile = () => farmRegistryClient.request("/v1/farmers/me/profile-export");
export const uploadFarmerDocument = async (file, documentType) => {
  void file;
  void documentType;
  return {
    status: "backend_pending",
    message: "Document upload backend pending",
  };
};
