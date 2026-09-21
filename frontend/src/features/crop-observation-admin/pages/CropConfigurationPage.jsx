import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createCrop, listCrops } from "@/features/crop-observation-admin/api/cropObservationAdminApi";
import SystemMediaField from "@/features/crop-observation-admin/components/SystemMediaField";

export default function CropConfigurationPage() {
  const [crops, setCrops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [newCrop, setNewCrop] = useState({
    crop_code: "",
    lifecycle_type: "ANNUAL",
    default_stage_strategy: "FIRST_STAGE",
  });

  async function load() {
    setLoading(true);
    setError("");
    try {
      setCrops(await listCrops());
    } catch (err) {
      setError(err?.message || "Could not load crops.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreateCrop() {
    if (!newCrop.crop_code.trim()) return;
    setCreating(true);
    try {
      await createCrop({ ...newCrop, crop_code: newCrop.crop_code.trim().toLowerCase() });
      setNewCrop({ crop_code: "", lifecycle_type: "ANNUAL", default_stage_strategy: "FIRST_STAGE" });
      await load();
    } catch (err) {
      setError(err?.message || "Could not create crop.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-black text-slate-950">Crop Configuration</h1>
      <p className="mt-1 text-sm text-slate-500">
        Configure stages, practices and fields farmers see in the crop diary.
      </p>

      {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
      {loading ? <p className="mt-4 text-sm text-slate-400">Loading…</p> : null}

      <div className="mt-6 space-y-3">
        {crops.map((crop) => (
          <div key={crop.crop_code} className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[180px_1fr_auto] md:items-center">
            <SystemMediaField
              targetType="CROP"
              targetId={crop.crop_id}
              assetRole="CROP_CARD_IMAGE"
              label="Crop card image"
              accept="image/jpeg,image/png,image/webp"
              compact
            />
            <div>
              <div className="font-bold text-slate-950">{crop.crop_code}</div>
              <div className="text-xs text-slate-500">{crop.lifecycle_type} · {crop.default_stage_strategy}</div>
              <span className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${crop.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{crop.is_active ? "Active" : "Inactive"}</span>
            </div>
            <Link to={`/admin/crop-observation/config/${crop.crop_code}`} className="rounded-lg bg-slate-900 px-4 py-2 text-center text-sm font-bold text-white hover:bg-slate-800">Configure crop</Link>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-xl border border-dashed border-slate-300 p-4">
        <p className="mb-3 text-sm font-semibold text-slate-700">Add a new crop</p>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="crop_code (e.g. groundnut)"
            value={newCrop.crop_code}
            onChange={(e) => setNewCrop((prev) => ({ ...prev, crop_code: e.target.value }))}
            className="w-56"
          />
          <select
            value={newCrop.lifecycle_type}
            onChange={(e) => setNewCrop((prev) => ({ ...prev, lifecycle_type: e.target.value }))}
            className="h-9 rounded-md border border-slate-200 px-2 text-sm"
          >
            <option value="ANNUAL">ANNUAL</option>
            <option value="PERENNIAL">PERENNIAL</option>
          </select>
          <select
            value={newCrop.default_stage_strategy}
            onChange={(e) => setNewCrop((prev) => ({ ...prev, default_stage_strategy: e.target.value }))}
            className="h-9 rounded-md border border-slate-200 px-2 text-sm"
          >
            <option value="FIRST_STAGE">FIRST_STAGE</option>
            <option value="CURRENT_STAGE">CURRENT_STAGE</option>
            <option value="SYSTEM_SUGGESTED">SYSTEM_SUGGESTED</option>
          </select>
          <Button onClick={handleCreateCrop} disabled={creating}>
            <Plus className="mr-1 h-4 w-4" /> Add crop
          </Button>
        </div>
      </div>
    </div>
  );
}
