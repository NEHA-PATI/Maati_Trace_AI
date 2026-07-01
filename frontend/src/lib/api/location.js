import { apiRequest } from "./client";
export const getStates = () => apiRequest("/api/location/states");
export const getDistricts = (stateName) => apiRequest(`/api/location/districts?state_name=${encodeURIComponent(stateName)}`);
export const getBlocks = (stateName, districtName) => apiRequest(`/api/location/blocks?state_name=${encodeURIComponent(stateName)}&district_name=${encodeURIComponent(districtName)}`);
export const validateLocation = (payload) => apiRequest("/api/location/validate", { method: "POST", body: JSON.stringify(payload) });
