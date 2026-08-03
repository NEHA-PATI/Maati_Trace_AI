import {
  locationClient,
} from "@/shared/api/serviceClients";

function queryString(values) {
  const params = new URLSearchParams();

  Object.entries(values).forEach(
    ([key, value]) => {
      if (
        value !== undefined
        && value !== null
        && String(value).trim() !== ""
      ) {
        params.set(key, String(value));
      }
    },
  );

  const query = params.toString();

  return query ? `?${query}` : "";
}

function listFromPayload(payload, keys) {
  if (Array.isArray(payload)) {
    return payload;
  }

  for (const key of keys) {
    if (Array.isArray(payload?.[key])) {
      return payload[key];
    }
  }

  return [];
}

export const profileLocationApi =
  Object.freeze({
    async getStates() {
      const payload =
        await locationClient.request(
          "/v1/location/states",
        );

      return listFromPayload(
        payload,
        ["states", "items", "results"],
      );
    },

    async getDistricts(
      stateName = "Odisha",
    ) {
      const payload =
        await locationClient.request(
          `/v1/location/districts${queryString({
            state_name: stateName,
          })}`,
        );

      return listFromPayload(
        payload,
        [
          "districts",
          "items",
          "results",
        ],
      );
    },

    async getBlocks({
      stateName = "Odisha",
      districtName,
    }) {
      if (!districtName) {
        return [];
      }

      const payload =
        await locationClient.request(
          `/v1/location/blocks${queryString({
            state_name: stateName,
            district_name: districtName,
          })}`,
        );

      return listFromPayload(
        payload,
        ["blocks", "items", "results"],
      );
    },
  });
