import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { useAuth } from "@/features/auth";
import { profileApi } from "@/features/profile/api/profileApi";

export function useProfile() {
  const {
    user,
    refreshSession,
  } = useAuth();

  const [envelope, setEnvelope] =
    useState(null);
  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState(null);
  const [saving, setSaving] =
    useState(false);
  const [exporting, setExporting] =
    useState(false);
  const [savedAt, setSavedAt] =
    useState(null);

  const loadProfile = useCallback(
    async () => {
      setLoading(true);
      setError(null);

      try {
        const payload =
          await profileApi.getMyProfile();

        setEnvelope(payload);
        return payload;
      } catch (profileError) {
        setError(profileError);
        throw profileError;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError(null);

    profileApi
      .getMyProfile()
      .then((payload) => {
        if (active) {
          setEnvelope(payload);
        }
      })
      .catch((profileError) => {
        if (active) {
          setError(profileError);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [user?.user_id]);

  const finishSave = useCallback(
    async () => {
      const nextEnvelope =
        await profileApi.getMyProfile();

      setEnvelope(nextEnvelope);
      setSavedAt(Date.now());

      try {
        await refreshSession();
      } catch (_error) {
        // Profile save succeeded; auth refresh is a projection sync best-effort.
      }

      return nextEnvelope;
    },
    [refreshSession],
  );

  const saveFarmerProfile =
    useCallback(
      async (payload) => {
        setSaving(true);
        setError(null);

        try {
          await profileApi
            .updateMyFarmerProfile(
              payload,
            );

          return await finishSave();
        } catch (saveError) {
          setError(saveError);
          throw saveError;
        } finally {
          setSaving(false);
        }
      },
      [finishSave],
    );

  const saveFpoProfile = useCallback(
    async (
      payload,
      setupRequired = false,
    ) => {
      setSaving(true);
      setError(null);

      try {
        if (setupRequired) {
          await profileApi
            .setupMyFpoProfile(
              payload,
            );
        } else {
          await profileApi
            .updateMyFpoProfile(
              payload,
            );
        }

        return await finishSave();
      } catch (saveError) {
        setError(saveError);
        throw saveError;
      } finally {
        setSaving(false);
      }
    },
    [finishSave],
  );

  const exportProfile =
    useCallback(async () => {
      setExporting(true);

      try {
        return await profileApi
          .exportMyProfile();
      } finally {
        setExporting(false);
      }
    }, []);

  return {
    user,
    envelope,
    profile: envelope?.profile || null,
    profileType:
      envelope?.profile_type
      || user?.role,
    onboardingStatus:
      envelope?.onboarding_status
      || "pending",
    completionPercentage:
      envelope?.completion_percentage
      ?? 0,
    missingFields:
      envelope?.missing_fields || [],
    setupRequired:
      Boolean(
        envelope?.setup_required,
      ),
    loading,
    error,
    saving,
    exporting,
    savedAt,
    loadProfile,
    saveFarmerProfile,
    saveFpoProfile,
    exportProfile,
  };
}
