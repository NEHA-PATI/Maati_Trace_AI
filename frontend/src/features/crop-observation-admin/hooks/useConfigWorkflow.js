import { useCallback, useEffect, useRef, useState } from "react";

import {
  cloneConfiguration,
  createDraftConfiguration,
  listConfigurations,
  listStages,
  publishConfiguration,
  validateConfiguration,
} from "../api/cropObservationAdminApi";

/**
 * Crop editor model: a single working copy, but the backend still uses versioned
 * config records for safety and rollback.
 *
 * Product UX is intentionally simplified to:
 * - open a crop
 * - edit the working copy
 * - publish when ready
 *
 * Internally, the app still creates a draft and may clone the published version,
 * but those mechanics are treated as implementation details, not exposed as a
 * user decision.
 */
export default function useConfigWorkflow(cropCode) {
  const [configs, setConfigs] = useState([]);
  const [workingConfigId, setWorkingConfigId] = useState("");
  const [publishedId, setPublishedId] = useState("");
  const [stages, setStages] = useState([]);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [justPublished, setJustPublished] = useState(null);
  const debounceRef = useRef(null);

  const published = configs.find((c) => c.config_version_id === publishedId);

  const refresh = useCallback(async () => {
    const list = await listConfigurations(cropCode);
    setConfigs(list);
    const pub = list.find((c) => c.status === "PUBLISHED");
    const working = list.find((c) => c.status === "DRAFT");
    setPublishedId(pub?.config_version_id || "");
    setWorkingConfigId((current) => current || working?.config_version_id || "");
    return { list, pub, draft: working };
  }, [cropCode]);

  const loadStagesFor = useCallback(async (configId) => {
    if (!configId) {
      setStages([]);
      return;
    }
    setStages(await listStages(configId));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { pub, draft } = await refresh();
      const activeConfigId = workingConfigId || draft?.config_version_id || pub?.config_version_id || "";
      await loadStagesFor(activeConfigId);
    } catch (err) {
      setError(err?.message || "Could not load configuration.");
    } finally {
      setLoading(false);
    }
  }, [refresh, loadStagesFor, workingConfigId]);

  useEffect(() => {
    load();
  }, [load]);

  const runValidation = useCallback(async () => {
    if (!workingConfigId) {
      setValidation(null);
      return;
    }
    try {
      setValidation(await validateConfiguration(workingConfigId));
    } catch {
      setValidation(null);
    }
  }, [workingConfigId]);

  useEffect(() => {
    if (!workingConfigId) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(runValidation, 600);
    return () => clearTimeout(debounceRef.current);
  }, [workingConfigId, stages, runValidation]);

  /**
   * Ensure an active working copy exists for the editor. This is the only place the
   * draft/clone mechanics live. Everything else can treat the crop editor as a
   * single working document.
   */
  const ensureWorkingCopy = useCallback(async () => {
    if (workingConfigId) return workingConfigId;
    setError("");

    try {
      const { pub, draft } = await refresh();
      if (draft?.config_version_id) {
        setWorkingConfigId(draft.config_version_id);
        await loadStagesFor(draft.config_version_id);
        return draft.config_version_id;
      }

      const next = pub
        ? await cloneConfiguration(pub.config_version_id)
        : await createDraftConfiguration(cropCode);

      setWorkingConfigId(next.config_version_id);
      await loadStagesFor(next.config_version_id);
      return next.config_version_id;
    } catch (err) {
      setError(err?.message || "Could not start editing.");
      return "";
    }
  }, [workingConfigId, refresh, cropCode, loadStagesFor]);

  const startEditing = ensureWorkingCopy;
  const ensureEditable = ensureWorkingCopy;

  const changed = useCallback(async () => {
    if (workingConfigId) await loadStagesFor(workingConfigId);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(runValidation, 400);
  }, [workingConfigId, loadStagesFor, runValidation]);

  const publish = useCallback(async () => {
    if (!workingConfigId) return null;
    setPublishing(true);
    setError("");
    try {
      const final = await validateConfiguration(workingConfigId);
      setValidation(final);
      if (!final.valid) return null;
      const row = await publishConfiguration(workingConfigId);
      setJustPublished(row.version_number);
      const { pub } = await refresh();
      await loadStagesFor(pub?.config_version_id || "");
      setWorkingConfigId("");
      return row;
    } catch (err) {
      if (Array.isArray(err?.fields) && err.fields.length) {
        setValidation({ valid: false, errors: err.fields, warnings: [] });
      }
      setError(err?.message || "Could not publish.");
      return null;
    } finally {
      setPublishing(false);
    }
  }, [workingConfigId, refresh, loadStagesFor]);

  return {
    configs,
    workingConfigId,
    published,
    publishedId,
    stages,
    validation,
    loading,
    error,
    publishing,
    justPublished,
    isEditing: Boolean(workingConfigId),
    readOnly: !workingConfigId,
    startEditing,
    ensureEditable,
    changed,
    publish,
    reload: load,
    setError,
    canPublish: Boolean(workingConfigId) && Boolean(validation?.valid) && !publishing,
  };
}
