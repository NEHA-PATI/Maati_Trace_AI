import {
  useEffect,
  useState,
} from "react";

import { profileLocationApi } from "@/features/profile/api/profileLocationApi";

function optionName(item) {
  return (
    item?.name
    || item?.state_name
    || item?.district_name
    || item?.block_name
    || String(item || "")
  );
}

export function useProfileLocations({
  stateName = "Odisha",
  districtName = "",
} = {}) {
  const [states, setStates] =
    useState([]);
  const [districts, setDistricts] =
    useState([]);
  const [blocks, setBlocks] =
    useState([]);
  const [loading, setLoading] =
    useState({
      states: false,
      districts: false,
      blocks: false,
    });
  const [error, setError] =
    useState(null);

  useEffect(() => {
    let active = true;

    setLoading((current) => ({
      ...current,
      states: true,
    }));

    profileLocationApi
      .getStates()
      .then((items) => {
        if (active) {
          setStates(items);
        }
      })
      .catch((locationError) => {
        if (active) {
          setError(locationError);
        }
      })
      .finally(() => {
        if (active) {
          setLoading((current) => ({
            ...current,
            states: false,
          }));
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    setLoading((current) => ({
      ...current,
      districts: true,
    }));

    profileLocationApi
      .getDistricts(stateName)
      .then((items) => {
        if (active) {
          setDistricts(items);
        }
      })
      .catch((locationError) => {
        if (active) {
          setError(locationError);
          setDistricts([]);
        }
      })
      .finally(() => {
        if (active) {
          setLoading((current) => ({
            ...current,
            districts: false,
          }));
        }
      });

    return () => {
      active = false;
    };
  }, [stateName]);

  useEffect(() => {
    let active = true;

    if (!districtName) {
      setBlocks([]);
      return () => {
        active = false;
      };
    }

    setLoading((current) => ({
      ...current,
      blocks: true,
    }));

    profileLocationApi
      .getBlocks({
        stateName,
        districtName,
      })
      .then((items) => {
        if (active) {
          setBlocks(items);
        }
      })
      .catch((locationError) => {
        if (active) {
          setError(locationError);
          setBlocks([]);
        }
      })
      .finally(() => {
        if (active) {
          setLoading((current) => ({
            ...current,
            blocks: false,
          }));
        }
      });

    return () => {
      active = false;
    };
  }, [stateName, districtName]);

  return {
    states,
    districts,
    blocks,
    loading,
    error,
    optionName,
  };
}
