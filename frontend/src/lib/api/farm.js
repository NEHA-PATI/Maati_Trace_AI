import { apiRequest } from "./client";
export const getFarm = (farmId) => apiRequest(`/api/farms/${farmId}`);
export const registerFarm = (payload) => apiRequest("/api/farms/register", { method: "POST", body: JSON.stringify(payload) });
export const getFarmsByFarmer = (farmerId) => apiRequest(`/api/farmers/${farmerId}/farms`);
