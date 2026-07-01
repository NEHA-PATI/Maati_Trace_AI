import { apiRequest } from "./client";
export const getFpos = () => apiRequest("/api/fpos");
export const getMyFpo = () => apiRequest("/api/fpos/me");
export const getFpo = (fpoId) => apiRequest(`/api/fpos/${fpoId}`);
export const getFpoSummary = (fpoId) => apiRequest(`/api/fpos/${fpoId}/summary`);
export const getFpoFarmers = (fpoId) => apiRequest(`/api/fpos/${fpoId}/farmers`);
export const getFpoFarms = (fpoId) => apiRequest(`/api/fpos/${fpoId}/farms`);
