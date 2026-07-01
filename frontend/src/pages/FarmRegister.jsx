import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getBlocks, getDistricts, getStates, validateLocation } from "@/lib/api/location";
import { createFarmer } from "@/lib/api/farmer";
import { registerFarm } from "@/lib/api/farm";
import { materializeFarmAnalysis } from "@/lib/api/hotStream";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const DEFAULT_POLYGON = {
  type: "Polygon",
  coordinates: [[[85.84, 19.81], [85.841, 19.81], [85.841, 19.811], [85.84, 19.811], [85.84, 19.81]]],
};

export default function FarmRegister() {
  const navigate = useNavigate();
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [blocks, setBlocks] = useState([]);
  const [form, setForm] = useState({ state_name: "Odisha", district_name: "", block_name: "", village_name: "", full_name: "", phone_number: "", farm_name: "", survey_number: "", runNow: true });
  const [status, setStatus] = useState({ loading: false, error: "", success: "" });

  useEffect(() => { getStates().then(setStates).catch(() => setStates([])); }, []);
  useEffect(() => {
    if (!form.state_name) return;
    getDistricts(form.state_name).then(setDistricts).catch(() => setDistricts([]));
  }, [form.state_name]);
  useEffect(() => {
    if (!form.state_name || !form.district_name) return;
    getBlocks(form.state_name, form.district_name).then(setBlocks).catch(() => setBlocks([]));
  }, [form.state_name, form.district_name]);

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const submit = async (event) => {
    event.preventDefault();
    setStatus({ loading: true, error: "", success: "" });
    try {
      const location = await validateLocation({
        state_name: form.state_name,
        district_name: form.district_name,
        block_name: form.block_name,
      });
      const farmer = await createFarmer({
        full_name: form.full_name,
        phone_number: form.phone_number || null,
        state_name: location.state_name,
        district_name: location.district_name,
        block_name: location.block_name,
        block_code: location.block_code,
        village_name: form.village_name || null,
      });
      const farm = await registerFarm({
        farmer_id: farmer.farmer_id,
        farm_name: form.farm_name || null,
        survey_number: form.survey_number || null,
        state_name: location.state_name,
        district_name: location.district_name,
        block_name: location.block_name,
        block_code: location.block_code,
        village_name: form.village_name || null,
        polygon: DEFAULT_POLYGON,
        h3_resolution: 12,
      });
      if (form.runNow) {
        await materializeFarmAnalysis(farm.farm_id, {
          start_date: "2026-01-01",
          end_date: "2026-07-01",
          max_cloud_cover: 30,
          h3_resolution: 12,
        }).catch(() => null);
      }
      setStatus({ loading: false, error: "", success: "Farm registered successfully." });
      navigate(`/land/${farm.farm_id}`);
    } catch (error) {
      setStatus({ loading: false, error: error.message || "Farm registration failed", success: "" });
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Farm Register</div>
        <h1 className="text-3xl font-black">Register farmer and farm</h1>
        <p className="text-sm text-muted-foreground">Location validation goes through the gateway and farm registration writes to the registry service only.</p>
      </div>
      <form onSubmit={submit} className="grid gap-4 rounded-3xl border bg-card p-5">
        <Input placeholder="Farmer full name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required />
        <Input placeholder="Phone number" value={form.phone_number} onChange={(e) => update("phone_number", e.target.value)} />
        <Input placeholder="Farm name" value={form.farm_name} onChange={(e) => update("farm_name", e.target.value)} />
        <Input placeholder="Survey number" value={form.survey_number} onChange={(e) => update("survey_number", e.target.value)} />
        <Input placeholder="Village name" value={form.village_name} onChange={(e) => update("village_name", e.target.value)} />
        <select className="rounded-xl border px-3 py-2" value={form.state_name} onChange={(e) => update("state_name", e.target.value)}>
          {states.map((state) => <option key={state.state_name || state.name} value={state.state_name || state.name}>{state.state_name || state.name}</option>)}
        </select>
        <select className="rounded-xl border px-3 py-2" value={form.district_name} onChange={(e) => update("district_name", e.target.value)} required>
          <option value="">Select district</option>
          {districts.map((district) => <option key={district.district_name || district.name} value={district.district_name || district.name}>{district.district_name || district.name}</option>)}
        </select>
        <select className="rounded-xl border px-3 py-2" value={form.block_name} onChange={(e) => update("block_name", e.target.value)} required>
          <option value="">Select block</option>
          {blocks.map((block) => <option key={block.block_name || block.name} value={block.block_name || block.name}>{block.block_name || block.name}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.runNow} onChange={(e) => update("runNow", e.target.checked)} /> Run latest analysis after registration</label>
        {status.error ? <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{status.error}</div> : null}
        {status.success ? <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{status.success}</div> : null}
        <Button type="submit" disabled={status.loading}>{status.loading ? "Registering..." : "Register farm"}</Button>
      </form>
    </div>
  );
}
