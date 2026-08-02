import { farmRegistryClient } from "@/shared/api/serviceClients";
export const createFpo = (payload) => farmRegistryClient.request("/v1/fpos", { method: "POST", body: JSON.stringify(payload) });
export const getFpos = () => farmRegistryClient.request("/v1/fpos");
export const getMyFpo = () => farmRegistryClient.request("/v1/fpos/me");
export const getFpo = (fpoId) => farmRegistryClient.request(`/v1/fpos/${fpoId}`);
export const getFpoSummary = (fpoId) => farmRegistryClient.request(`/v1/fpos/${fpoId}/summary`);
export const getFpoFarmers = (fpoId) => farmRegistryClient.request(`/v1/fpos/${fpoId}/farmers`);
export const getFpoFarms = (fpoId) => farmRegistryClient.request(`/v1/fpos/${fpoId}/farms`);
