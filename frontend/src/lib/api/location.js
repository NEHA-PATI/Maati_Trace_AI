import { locationClient } from "./client";

function extractArray(payload, keys) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  for (const key of keys) {
    if (Array.isArray(payload[key])) return payload[key];
  }
  return [];
}

export function normalizeStates(response) {
  return extractArray(response, ["items", "states", "data"]).map((item) => ({
    state_code: item.state_code ?? item.code ?? null,
    state_name: item.state_name ?? item.name ?? String(item),
  }));
}

export function normalizeDistricts(response) {
  return extractArray(response, ["items", "districts", "data"]).map((item) => ({
    district_code: item.district_code ?? item.code ?? null,
    district_name: item.district_name ?? item.name ?? String(item),
    state_name: item.state_name ?? null,
  }));
}

export function normalizeBlocks(response) {
  return extractArray(response, ["items", "blocks", "data"]).map((item) => ({
    block_code: item.block_code ?? item.code ?? null,
    block_name: item.block_name ?? item.name ?? String(item),
    district_name: item.district_name ?? null,
  }));
}

export async function getStates() {
  return normalizeStates(await locationClient.request("/v1/states"));
}

export async function getDistricts(stateName) {
  return normalizeDistricts(
    await locationClient.request(`/v1/districts?state_name=${encodeURIComponent(stateName)}`),
  );
}

export async function getBlocks(stateName, districtName) {
  return normalizeBlocks(
    await locationClient.request(
      `/v1/blocks?state_name=${encodeURIComponent(stateName)}&district_name=${encodeURIComponent(districtName)}`,
    ),
  );
}

export function validateLocation(payload) {
  return locationClient.request("/v1/location/validate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
