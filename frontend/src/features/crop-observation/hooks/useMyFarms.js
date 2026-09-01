import { useEffect, useState } from "react";

import { getFarmerFarms, getMyFarmerProfile } from "@/lib/api/farmer";

export function useMyFarms() {
  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const profile = await getMyFarmerProfile();
        const list = await getFarmerFarms(profile.farmer_id);
        if (!cancelled) setFarms(Array.isArray(list) ? list : []);
      } catch (err) {
        if (!cancelled) setError(err?.message || "Could not load your farms.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { farms, loading, error };
}
