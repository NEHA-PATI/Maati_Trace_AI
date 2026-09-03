import { useCallback, useEffect, useRef, useState } from "react";

import { getStageScreen, saveDailyStatus } from "@/features/crop-observation/api/cropObservationApi";
import { cacheGet, cacheInvalidate, cacheSet } from "@/features/crop-observation/cache";

function screenKey(cropCycleId, stageCode, locale) {
  return `screen:${cropCycleId}:${stageCode}:${locale}`;
}

/** Prefetch a stage screen into cache (call on crop-card press for instant nav). */
export function prefetchStageScreen(cropCycleId, stageCode, locale) {
  const key = screenKey(cropCycleId, stageCode, locale);
  if (cacheGet(key) !== undefined) return;
  getStageScreen(cropCycleId, stageCode, locale)
    .then((data) => cacheSet(key, data))
    .catch(() => {});
}

/**
 * Loads a stage screen with stale-while-revalidate caching and applies daily
 * status changes optimistically — the selection paints immediately and only the
 * status pill (not the whole page) reflects the in-flight save.
 */
export function useCropScreen(cropCycleId, stageCode, locale) {
  const key = screenKey(cropCycleId, stageCode, locale);
  const [screen, setScreen] = useState(() => cacheGet(key));
  const [loading, setLoading] = useState(!screen);
  const [error, setError] = useState("");
  const [statusSave, setStatusSave] = useState("idle"); // idle | saving | saved | error
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const load = useCallback(
    async ({ revalidateOnly = false } = {}) => {
      const cached = cacheGet(key);
      if (cached) {
        setScreen(cached);
        setLoading(false);
      } else if (!revalidateOnly) {
        setLoading(true);
      }
      setError("");
      try {
        const data = await getStageScreen(cropCycleId, stageCode, locale);
        cacheSet(key, data);
        if (mounted.current) setScreen(data);
      } catch (err) {
        if (mounted.current && !cacheGet(key)) {
          setError(err?.message || "Could not load this stage.");
        }
      } finally {
        if (mounted.current) setLoading(false);
      }
    },
    [cropCycleId, stageCode, locale, key],
  );

  useEffect(() => {
    load({ revalidateOnly: Boolean(cacheGet(key)) });
  }, [load, key]);

  const setStatus = useCallback(
    async (code, newClientEntryId) => {
      setStatusSave("saving");
      setScreen((prev) =>
        prev
          ? { ...prev, today: { ...prev.today, observation: { ...(prev.today.observation || {}), crop_status: code } } }
          : prev,
      );
      try {
        const saved = await saveDailyStatus(cropCycleId, stageCode, {
          client_entry_id: newClientEntryId,
          crop_status: code,
          captured_at_client: new Date().toISOString(),
        });
        cacheInvalidate(`screen:${cropCycleId}:`);
        cacheInvalidate(`history:${cropCycleId}`);
        if (mounted.current) {
          setStatusSave("saved");
          // Merge the id in immediately so photo/voice capture for today's
          // entry can enable itself without waiting on the full reload.
          setScreen((prev) =>
            prev
              ? {
                  ...prev,
                  today: {
                    ...prev.today,
                    observation: {
                      ...(prev.today.observation || {}),
                      daily_observation_id: saved.daily_observation_id,
                      crop_status: saved.crop_status,
                    },
                  },
                }
              : prev,
          );
          load({ revalidateOnly: true });
        }
      } catch (err) {
        if (mounted.current) {
          setStatusSave("error");
          setError(err?.message || "");
        }
      }
    },
    [cropCycleId, stageCode, load],
  );

  return { screen, loading, error, statusSave, reload: load, setStatus };
}
