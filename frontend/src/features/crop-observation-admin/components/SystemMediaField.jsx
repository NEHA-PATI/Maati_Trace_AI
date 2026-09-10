import { useCallback, useEffect, useState } from "react";
import { Image as ImageIcon, Music2, RefreshCw, Trash2, Upload } from "lucide-react";

import {
  deleteSystemMediaBinding,
  listSystemMedia,
  resolveCropObservationServiceUrl,
  uploadSystemMedia,
} from "@/features/crop-observation-admin/api/cropObservationAdminApi";

export default function SystemMediaField({
  targetType,
  targetId,
  assetRole,
  locale = null,
  label,
  accept,
  readOnly = false,
  compact = false,
  onChanged,
}) {
  const [asset, setAsset] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!targetId) return;
    try {
      const rows = await listSystemMedia({
        target_type: targetType,
        target_id: targetId,
        asset_role: assetRole,
        locale: locale || undefined,
        limit: 10,
      });
      setAsset(rows?.[0] || null);
    } catch {
      setAsset(null);
    }
  }, [assetRole, locale, targetId, targetType]);

  useEffect(() => {
    load();
  }, [load]);

  async function upload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await uploadSystemMedia({
        file,
        targetType,
        targetId,
        assetRole,
        locale,
      });
      await load();
      onChanged?.();
    } catch (err) {
      setError(err?.message || "Could not upload media.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!asset?.binding_id) return;
    setBusy(true);
    setError("");
    try {
      await deleteSystemMediaBinding(asset.binding_id);
      setAsset(null);
      onChanged?.();
    } catch (err) {
      setError(err?.message || "Could not remove media.");
    } finally {
      setBusy(false);
    }
  }

  const url = asset?.content_url ? resolveCropObservationServiceUrl(asset.content_url) : "";
  const isAudio = assetRole === "INSTRUCTION_AUDIO";

  return (
    <div className={`rounded-xl border border-slate-200 bg-white ${compact ? "p-2.5" : "p-3"}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          {isAudio ? <Music2 className="h-4 w-4 text-emerald-700" /> : <ImageIcon className="h-4 w-4 text-emerald-700" />}
          <div className="min-w-0">
            <p className="truncate text-xs font-bold text-slate-700">{label}</p>
            {asset ? <p className="truncate text-[11px] text-slate-400">{asset.storage_backend} · {asset.mime_type}</p> : <p className="text-[11px] text-amber-600">Not configured</p>}
          </div>
        </div>
        {!readOnly ? (
          <div className="flex shrink-0 items-center gap-1">
            <label className="inline-flex h-8 cursor-pointer items-center gap-1 rounded-lg border bg-white px-2 text-xs font-bold text-slate-700 hover:bg-slate-50">
              {asset ? <RefreshCw className="h-3.5 w-3.5" /> : <Upload className="h-3.5 w-3.5" />}
              {busy ? "Working…" : asset ? "Replace" : "Upload"}
              <input type="file" accept={accept} className="hidden" disabled={busy} onChange={upload} />
            </label>
            {asset ? (
              <button type="button" disabled={busy} onClick={remove} className="grid h-8 w-8 place-items-center rounded-lg border text-slate-400 hover:text-rose-600" aria-label="Remove media">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      {asset && url ? (
        <div className="mt-2">
          {isAudio ? (
            <audio controls preload="metadata" src={url} className="h-9 w-full" />
          ) : (
            <img src={url} alt="Configured media" className={`${compact ? "h-20" : "h-32"} w-full rounded-lg bg-slate-100 object-cover`} />
          )}
        </div>
      ) : null}
      {error ? <p className="mt-2 text-xs font-medium text-rose-600">{error}</p> : null}
    </div>
  );
}
