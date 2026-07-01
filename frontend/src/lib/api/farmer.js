import { apiRequest } from "./client";
export const getMyFarmerProfile = () => apiRequest("/api/farmers/me");
export const getFarmer = (farmerId) => apiRequest(`/api/farmers/${farmerId}`);
export const getFarmerSummary = (farmerId) => apiRequest(`/api/farmers/${farmerId}/summary`);
export const getFarmerFarms = (farmerId) => apiRequest(`/api/farmers/${farmerId}/farms`);
export const createFarmer = (payload) => apiRequest("/api/farmers", { method: "POST", body: JSON.stringify(payload) });
