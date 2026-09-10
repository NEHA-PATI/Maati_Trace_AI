import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Activity, Database, Play, Plus, RefreshCw, Save, Satellite,
  Sprout, Layers, Server,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  cloneCropConfiguration,
  cloneCropProfile,
  cloneFormula,
  createCropProfile,
  createFormula,
  deleteCropProfile,
  deleteFormula,
  publishAllFormulasForProfile,
  seedFormulasIntoProfile,
  getAdminCropProfiles,
  getAdminFormulas,
  getComponentCatalog,
  getFeatureProcessingRuns,
  getFeatureProcessingSources,
  getFeatureProcessingSummary,
  publishCropProfile,
  publishFormula,
  updateCropProfile,
  updateFormula,
  getAdminMetricContent,
  updateMetricContent,
  cloneMetricContent,
  publishMetricContent,
} from "@/lib/api/featureProcessingAdmin";
import { materializeFarmIntelligence } from "@/lib/api/analytics";
import { getAllServiceHealth } from "@/lib/api/health";

const DOMAINS = [
  ["feature-engine", "Feature Engine", Sprout],
  ["raster", "Raster Management", Satellite],
  ["farm-registry", "Farm Registry", Database],
  ["analytics", "Analytics", Activity],
  ["hot-stream", "Hot Stream", Layers],
];

const FE_TABS = [
  ["overview", "Overview"],
  ["runs", "Processing Runs"],
  ["profiles", "Crop Profiles"],
  ["formulas", "Formula Registry"],
  ["components", "Component Catalog"],
  ["content", "Metric Content"],
];

const RASTER_ADAPTERS = [
  ["sentinel_2_l2a", "Sentinel-2 L2A", "optical / vegetation & moisture indices", "h3_sentinel2_features"],
  ["sentinel_1_rtc", "Sentinel-1 RTC", "SAR VV/VH backscatter", "h3_sentinel1_features"],
  ["landsat_c2_l2", "Landsat C2 L2", "surface temperature + optical", "h3_landsat_features"],
  ["gpm_imerg", "GPM IMERG", "daily precipitation", "farm_weather_observations"],
  ["era5_land", "ERA5-Land", "reanalysis temp + soil water layers", "farm_reanalysis_daily"],
  ["smap_l4_sm", "SMAP L4", "surface + root-zone soil moisture", "farm_smap_observations"],
  ["modis_et", "MODIS ET/PET", "8-day evapotranspiration", "farm_modis_et_observations"],
  ["modis_lai_fpar", "MODIS LAI/FPAR", "leaf area + fraction absorbed PAR", "farm_modis_vegetation_observations"],
  ["cop_dem_glo30", "Copernicus DEM 30m", "elevation + slope + aspect", "h3_terrain_features"],
  ["esa_worldcover", "ESA WorldCover", "landcover class fractions", "h3_landcover_features"],
  ["jrc_surface_water", "JRC Global Surface Water", "historic water occurrence", "h3_surface_water_features"],
  ["soilgrids_v2", "SoilGrids v2", "pH, SOC, N, CEC, texture, BD", "h3_soilgrids_features"],
  ["weather_forecast", "Weather Forecast", "VPD, ET0, precip forecast", "farm_weather_forecasts"],
];

function JsonField({ label, value, onChange, rows = 6, disabled = false }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-semibold text-slate-600">{label}</Label>
      <textarea
        rows={rows}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-xs text-slate-700 outline-none focus:border-emerald-400 disabled:bg-slate-50 disabled:text-slate-500"
      />
    </div>
  );
}

function parseJson(value) {
  try {
    return JSON.parse(value || "{}");
  } catch {
    throw new Error("One of the JSON configuration fields is invalid.");
  }
}

function formatDate(value) {
  if (!value) return "--";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
}

function SummaryCard({ label, value, detail }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-800">{value ?? 0}</p>
      {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
    </div>
  );
}

function ProfileEditor({ profile, onSaved }) {
  const isExisting = Boolean(profile?.profile_id);
  const canEdit = !isExisting || profile?.status === "draft";
  const [form, setForm] = useState(() => ({
    crop_code: profile?.crop_code || "",
    crop_name: profile?.crop_name || "",
    profile_version: profile?.profile_version || "",
    crop_type: profile?.crop_type || "crop",
    minimum_history_days: profile?.minimum_history_days ?? 60,
    preferred_history_days: profile?.preferred_history_days ?? 180,
    temporal_windows: JSON.stringify(profile?.temporal_windows || {}, null, 2),
    root_zone_weights: JSON.stringify(profile?.root_zone_weights || {}, null, 2),
    soil_ranges: JSON.stringify(profile?.soil_ranges || {}, null, 2),
    normalization: JSON.stringify(profile?.normalization || {}, null, 2),
    growth_config: JSON.stringify(profile?.growth_config || {}, null, 2),
    metadata: JSON.stringify(profile?.metadata || { validation_status: "engineering_default_requires_field_calibration" }, null, 2),
  }));
  const [error, setError] = useState("");
  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  async function save() {
    setError("");
    try {
      const payload = {
        ...(isExisting ? {} : { crop_code: form.crop_code, profile_version: form.profile_version }),
        crop_name: form.crop_name,
        crop_type: form.crop_type,
        minimum_history_days: Number(form.minimum_history_days),
        preferred_history_days: Number(form.preferred_history_days),
        temporal_windows: parseJson(form.temporal_windows),
        root_zone_weights: parseJson(form.root_zone_weights),
        soil_ranges: parseJson(form.soil_ranges),
        normalization: parseJson(form.normalization),
        growth_config: parseJson(form.growth_config),
        metadata: parseJson(form.metadata),
      };
      if (isExisting) await updateCropProfile(profile.profile_id, payload);
      else await createCropProfile(payload);
      onSaved?.();
    } catch (err) {
      setError(err?.message || "Unable to save crop profile.");
    }
  }

  return (
    <div className="space-y-4 rounded-2xl border border-emerald-100 bg-emerald-50/30 p-4">
      <div className="grid gap-3 md:grid-cols-3">
        <div><Label className="text-xs">Crop code</Label><Input disabled={isExisting} value={form.crop_code} onChange={(e) => update("crop_code", e.target.value)} /></div>
        <div><Label className="text-xs">Crop name</Label><Input disabled={!canEdit} value={form.crop_name} onChange={(e) => update("crop_name", e.target.value)} /></div>
        <div><Label className="text-xs">Profile version</Label><Input disabled={isExisting} value={form.profile_version} onChange={(e) => update("profile_version", e.target.value)} /></div>
        <div><Label className="text-xs">Crop type</Label><Input disabled={!canEdit} value={form.crop_type} onChange={(e) => update("crop_type", e.target.value)} /></div>
        <div><Label className="text-xs">Minimum history days</Label><Input disabled={!canEdit} type="number" value={form.minimum_history_days} onChange={(e) => update("minimum_history_days", e.target.value)} /></div>
        <div><Label className="text-xs">Preferred history days</Label><Input disabled={!canEdit} type="number" value={form.preferred_history_days} onChange={(e) => update("preferred_history_days", e.target.value)} /></div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <JsonField label="Temporal windows JSON" value={form.temporal_windows} disabled={!canEdit} onChange={(v) => update("temporal_windows", v)} />
        <JsonField label="Root-zone weights JSON (sum 1.0)" value={form.root_zone_weights} disabled={!canEdit} onChange={(v) => update("root_zone_weights", v)} />
        <JsonField label="Soil ranges JSON" value={form.soil_ranges} disabled={!canEdit} onChange={(v) => update("soil_ranges", v)} />
        <JsonField label="Normalization JSON" value={form.normalization} disabled={!canEdit} onChange={(v) => update("normalization", v)} />
        <JsonField label="Growth config JSON" value={form.growth_config} disabled={!canEdit} onChange={(v) => update("growth_config", v)} />
        <JsonField label="Metadata JSON" value={form.metadata} disabled={!canEdit} onChange={(v) => update("metadata", v)} />
      </div>
      {error && <p className="text-xs font-medium text-rose-600">{error}</p>}
      {!canEdit && <p className="text-xs text-slate-500">Published profiles are immutable. Clone to a new version, edit the draft, publish matching formula drafts, then publish the profile as the production switch.</p>}
      {canEdit && <Button onClick={save} className="rounded-xl bg-emerald-600 text-white hover:bg-emerald-700"><Save className="mr-2 h-4 w-4" />Save draft</Button>}
    </div>
  );
}

function FormulaEditor({ formula, components, onSaved }) {
  const isExisting = Boolean(formula?.formula_id);
  const canEdit = !isExisting || formula?.status === "draft";
  const [form, setForm] = useState(() => ({
    crop_code: formula?.crop_code || "",
    prediction_key: formula?.prediction_key || "",
    display_name: formula?.display_name || "",
    formula_version: formula?.formula_version || "",
    crop_profile_version: formula?.crop_profile_version || "",
    score_direction: formula?.score_direction || "risk",
    execution_order: formula?.execution_order ?? 100,
    component_weights: JSON.stringify(formula?.component_weights || {}, null, 2),
    thresholds: JSON.stringify(formula?.thresholds || {}, null, 2),
    parameters: JSON.stringify(formula?.parameters || {}, null, 2),
    description: formula?.description || "",
    metadata: JSON.stringify(formula?.metadata || { validation_status: "engineering_default" }, null, 2),
  }));
  const [error, setError] = useState("");
  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  async function save() {
    setError("");
    try {
      const common = {
        display_name: form.display_name,
        crop_profile_version: form.crop_profile_version,
        formula_type: "weighted_components",
        score_direction: form.score_direction,
        execution_order: Number(form.execution_order),
        component_weights: parseJson(form.component_weights),
        thresholds: parseJson(form.thresholds),
        parameters: parseJson(form.parameters),
        description: form.description || null,
        metadata: parseJson(form.metadata),
      };
      if (isExisting) await updateFormula(formula.formula_id, common);
      else await createFormula({ ...common, crop_code: form.crop_code, prediction_key: form.prediction_key, formula_version: form.formula_version });
      onSaved?.();
    } catch (err) {
      setError(err?.message || "Unable to save formula.");
    }
  }

  return (
    <div className="space-y-4 rounded-2xl border border-blue-100 bg-blue-50/30 p-4">
      <div className="grid gap-3 md:grid-cols-3">
        <div><Label className="text-xs">Crop code</Label><Input disabled={isExisting} value={form.crop_code} onChange={(e) => update("crop_code", e.target.value)} /></div>
        <div><Label className="text-xs">Prediction key</Label><Input disabled={isExisting} value={form.prediction_key} onChange={(e) => update("prediction_key", e.target.value)} /></div>
        <div><Label className="text-xs">Display name</Label><Input disabled={!canEdit} value={form.display_name} onChange={(e) => update("display_name", e.target.value)} /></div>
        <div><Label className="text-xs">Formula version</Label><Input disabled={isExisting} value={form.formula_version} onChange={(e) => update("formula_version", e.target.value)} /></div>
        <div><Label className="text-xs">Crop profile version</Label><Input disabled={!canEdit} value={form.crop_profile_version} onChange={(e) => update("crop_profile_version", e.target.value)} /></div>
        <div>
          <Label className="text-xs">Score direction</Label>
          <select disabled={!canEdit} className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm" value={form.score_direction} onChange={(e) => update("score_direction", e.target.value)}>
            <option value="risk">risk</option>
            <option value="condition">condition</option>
          </select>
        </div>
        <div><Label className="text-xs">Execution order</Label><Input disabled={!canEdit} type="number" value={form.execution_order} onChange={(e) => update("execution_order", e.target.value)} /></div>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600">
        <strong>Allowed safe component keys:</strong> {components.map((c) => c.component_key).join(", ")} plus <code>prediction:&lt;key&gt;</code> and <code>prediction_inverse:&lt;key&gt;</code>.
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <JsonField label="Component weights JSON (must sum to 1.0)" value={form.component_weights} disabled={!canEdit} onChange={(v) => update("component_weights", v)} rows={9} />
        <JsonField label="Thresholds JSON" value={form.thresholds} disabled={!canEdit} onChange={(v) => update("thresholds", v)} />
        <JsonField label="Parameters JSON" value={form.parameters} disabled={!canEdit} onChange={(v) => update("parameters", v)} />
        <JsonField label="Metadata JSON" value={form.metadata} disabled={!canEdit} onChange={(v) => update("metadata", v)} />
      </div>
      <div><Label className="text-xs">Description</Label><Input disabled={!canEdit} value={form.description} onChange={(e) => update("description", e.target.value)} /></div>
      {error && <p className="text-xs font-medium text-rose-600">{error}</p>}
      {!canEdit && <p className="text-xs text-slate-500">Published formulas are immutable. Clone a new version; formula drafts can be published/staged before the crop profile, then activated together when the profile publishes.</p>}
      {canEdit && <Button onClick={save} className="rounded-xl bg-blue-600 text-white hover:bg-blue-700"><Save className="mr-2 h-4 w-4" />Save draft</Button>}
    </div>
  );
}

function MetricContentEditor({ content, onSaved }) {
  const [form, setForm] = useState(() => ({
    display_name: content?.display_name || "",
    signal_meaning: content?.signal_meaning || "",
    ranges: JSON.stringify(content?.ranges || {}, null, 2),
    messages: JSON.stringify(content?.messages || {}, null, 2),
    field_interpretation: JSON.stringify(content?.field_interpretation || {}, null, 2),
  }));
  const [error, setError] = useState("");
  const update = (key, value) => setForm((previous) => ({ ...previous, [key]: value }));

  async function save() {
    setError("");
    try {
      await updateMetricContent(content.content_id, {
        display_name: form.display_name,
        signal_meaning: form.signal_meaning,
        ranges: parseJson(form.ranges),
        messages: parseJson(form.messages),
        field_interpretation: parseJson(form.field_interpretation),
      });
      onSaved?.();
    } catch (err) {
      setError(err?.message || "Unable to save metric content draft.");
    }
  }

  return (
    <div className="space-y-4 rounded-2xl border border-amber-100 bg-amber-50/30 p-4">
      <div className="grid gap-3 md:grid-cols-2">
        <div><Label className="text-xs">Metric name</Label><Input value={form.display_name} onChange={(e) => update("display_name", e.target.value)} /></div>
        <div><Label className="text-xs">Scope</Label><Input disabled value={`${content.crop_code} · ${content.content_version}`} /></div>
      </div>
      <div><Label className="text-xs">Signal meaning shown to farmers</Label><textarea rows={3} value={form.signal_meaning} onChange={(e) => update("signal_meaning", e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm" /></div>
      <div className="grid gap-4 lg:grid-cols-3">
        <JsonField label="Score ranges JSON (logic-compatible labels/messages)" value={form.ranges} onChange={(v) => update("ranges", v)} rows={12} />
        <JsonField label="Status messages JSON" value={form.messages} onChange={(v) => update("messages", v)} rows={12} />
        <JsonField label="Field interpretation JSON" value={form.field_interpretation} onChange={(v) => update("field_interpretation", v)} rows={12} />
      </div>
      {error && <p className="text-xs font-medium text-rose-600">{error}</p>}
      <Button onClick={save} className="rounded-xl bg-amber-600 text-white hover:bg-amber-700"><Save className="mr-2 h-4 w-4" />Save content draft</Button>
    </div>
  );
}

function ServiceHealthStrip({ health }) {
  const entries = Object.entries(health || {});
  if (!entries.length) return null;
  return (
    <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
      {entries.map(([name, value]) => {
        const ok = value?.status === "live" || value?.status === "ready";
        return (
          <div key={name} className="flex items-center gap-2 rounded-xl border border-slate-100 bg-white p-3 text-xs shadow-sm">
            <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-500" : "bg-rose-500"}`} />
            <span className="font-semibold capitalize text-slate-700">{name}</span>
            <span className="ml-auto text-slate-400">{value?.status || "down"}</span>
          </div>
        );
      })}
    </div>
  );
}

function RunTable({ runs }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-sm">
      <table className="w-full text-xs">
        <thead className="bg-slate-50">
          <tr>{["Farm", "Job", "Stage", "Status", "Started", "Finished", "Error"].map((h) => <th key={h} className="px-3 py-2 text-left text-slate-400">{h}</th>)}</tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.job_id} className="border-t">
              <td className="px-3 py-2 font-mono">{String(run.farm_id || "--").slice(0, 8)}</td>
              <td className="px-3 py-2">{run.job_type}</td>
              <td className="px-3 py-2">{run.current_stage || "--"}</td>
              <td className="px-3 py-2 font-semibold">{run.status}</td>
              <td className="px-3 py-2">{formatDate(run.started_at)}</td>
              <td className="px-3 py-2">{formatDate(run.finished_at)}</td>
              <td className="max-w-[320px] truncate px-3 py-2 text-rose-600">{run.error_message || "--"}</td>
            </tr>
          ))}
          {!runs.length && <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-400">No runs recorded.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export default function SystemManagementPage() {
  const [domain, setDomain] = useState("feature-engine");
  const [feTab, setFeTab] = useState("overview");

  const [summary, setSummary] = useState({});
  const [runs, setRuns] = useState([]);
  const [sources, setSources] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [formulas, setFormulas] = useState([]);
  const [components, setComponents] = useState([]);
  const [metricContent, setMetricContent] = useState([]);
  const [health, setHealth] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editingProfile, setEditingProfile] = useState(null);
  const [editingFormula, setEditingFormula] = useState(null);
  const [editingContent, setEditingContent] = useState(null);
  const [newProfile, setNewProfile] = useState(false);
  const [newFormula, setNewFormula] = useState(false);
  const [cloneCrop, setCloneCrop] = useState({ source_crop_code: "coconut", target_crop_code: "", target_crop_name: "", target_profile_version: "", formula_version_suffix: "v1" });
  const [trigger, setTrigger] = useState({ farm_id: "", start_date: "", end_date: "", latest_only: false });
  const [triggerResult, setTriggerResult] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [summaryValue, runValues, sourceValues, profileValues, formulaValues, componentValues, contentValues, healthValue] = await Promise.all([
        getFeatureProcessingSummary().catch(() => ({})),
        getFeatureProcessingRuns(150).catch(() => []),
        getFeatureProcessingSources().catch(() => []),
        getAdminCropProfiles().catch(() => []),
        getAdminFormulas().catch(() => []),
        getComponentCatalog().catch(() => []),
        getAdminMetricContent().catch(() => []),
        getAllServiceHealth().catch(() => ({})),
      ]);
      setSummary(summaryValue || {});
      setRuns(runValues || []);
      setSources(sourceValues || []);
      setProfiles(profileValues || []);
      setFormulas(formulaValues || []);
      setComponents(componentValues || []);
      setMetricContent(contentValues || []);
      setHealth(healthValue || {});
    } catch (err) {
      setError(err?.message || "Unable to load system management console.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const activeProfiles = useMemo(() => profiles.filter((p) => p.is_active), [profiles]);
  const sourceByKey = useMemo(() => Object.fromEntries(sources.map((s) => [s.dataset_key, s])), [sources]);
  const runsFor = (types) => runs.filter((r) => types.includes(r.job_type));

  async function runIntelligence() {
    setTriggerResult(null);
    setError("");
    try {
      if (!trigger.farm_id || !trigger.start_date || !trigger.end_date) throw new Error("Farm ID, start date and end date are required.");
      const result = await materializeFarmIntelligence(trigger.farm_id, {
        start_date: trigger.start_date, end_date: trigger.end_date, latest_only: trigger.latest_only, force_refresh: false,
      });
      setTriggerResult(result);
      await load();
    } catch (err) {
      setError(err?.message || "Processing request failed.");
    }
  }

  return (
    <div className="mx-auto max-w-[1500px] space-y-5 p-4 md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link to="/admin"><Button variant="outline" size="sm" className="rounded-xl"><ArrowLeft className="mr-1 h-4 w-4" />Admin</Button></Link>
          <div>
            <h1 className="text-xl font-bold text-slate-800">System Management</h1>
            <p className="text-xs text-slate-500">Configure and monitor the platform without touching code.</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={load} className="rounded-xl"><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button>
      </div>

      <div className="flex flex-wrap gap-2 rounded-2xl border border-slate-100 bg-white p-2 shadow-sm">
        {DOMAINS.map((def) => {
          const key = def[0];
          const label = def[1];
          const Icon = def[2];
          return (
            <button key={key} onClick={() => setDomain(key)} className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold ${domain === key ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}>
              <Icon className="h-4 w-4" />{label}
            </button>
          );
        })}
      </div>

      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {loading && <div className="rounded-xl border bg-white p-5 text-sm text-slate-500">Loading…</div>}

      {/* ---------------- FEATURE ENGINE ---------------- */}
      {!loading && domain === "feature-engine" && (
        <>
          <div className="rounded-2xl border border-amber-100 bg-amber-50 p-3 text-xs text-amber-800">
            Refresh reloads telemetry only — it does <strong>not</strong> re-run satellite ingestion or feature engineering. Published profile/formula versions are immutable; clone a new version to change production behaviour.
          </div>
          <div className="flex flex-wrap gap-2 rounded-2xl border border-slate-100 bg-white p-2 shadow-sm">
            {FE_TABS.map(([key, label]) => (
              <button key={key} onClick={() => setFeTab(key)} className={`rounded-xl px-4 py-2 text-xs font-semibold ${feTab === key ? "bg-emerald-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}>{label}</button>
            ))}
          </div>

          {feTab === "overview" && (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <SummaryCard label="Jobs (24h)" value={summary.jobs_24h} />
                <SummaryCard label="Running" value={summary.jobs_running} />
                <SummaryCard label="Feature rows" value={summary.engineered_feature_rows} detail={`${summary.farms_with_features || 0} farms`} />
                <SummaryCard label="Calculated results" value={summary.calculated_prediction_rows} />
                <SummaryCard label="Grid scores" value={summary.grid_calculation_rows} />
              </div>
              <div className="grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
                <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
                  <div className="border-b px-4 py-3 font-semibold text-slate-800">Source readiness</div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-50 text-slate-400"><tr><th className="px-3 py-2 text-left">Dataset</th><th className="px-3 py-2 text-right">Rows</th><th className="px-3 py-2 text-right">Farms</th><th className="px-3 py-2 text-left">Latest</th></tr></thead>
                      <tbody>{sources.map((s) => <tr key={s.dataset_key} className="border-t"><td className="px-3 py-2 font-semibold">{s.dataset_key}</td><td className="px-3 py-2 text-right">{s.row_count}</td><td className="px-3 py-2 text-right">{s.farm_count}</td><td className="px-3 py-2">{formatDate(s.latest_observation)}</td></tr>)}</tbody>
                    </table>
                  </div>
                </div>
                <div className="space-y-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                  <div className="flex items-center gap-2 font-semibold text-slate-800"><Play className="h-4 w-4 text-emerald-600" />Run crop intelligence</div>
                  <div><Label className="text-xs">Farm ID</Label><Input value={trigger.farm_id} onChange={(e) => setTrigger((p) => ({ ...p, farm_id: e.target.value }))} placeholder="UUID" /></div>
                  <div className="grid grid-cols-2 gap-2">
                    <div><Label className="text-xs">Start</Label><Input type="date" value={trigger.start_date} onChange={(e) => setTrigger((p) => ({ ...p, start_date: e.target.value }))} /></div>
                    <div><Label className="text-xs">End</Label><Input type="date" value={trigger.end_date} onChange={(e) => setTrigger((p) => ({ ...p, end_date: e.target.value }))} /></div>
                  </div>
                  <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={trigger.latest_only} onChange={(e) => setTrigger((p) => ({ ...p, latest_only: e.target.checked }))} />Latest anchor only</label>
                  <Button onClick={runIntelligence} className="w-full rounded-xl bg-emerald-600 text-white">Run Feature + Formula Processing</Button>
                  {triggerResult && <pre className="max-h-48 overflow-auto rounded-xl bg-slate-950 p-3 text-[10px] text-emerald-200">{JSON.stringify(triggerResult, null, 2)}</pre>}
                </div>
              </div>
            </>
          )}

          {feTab === "runs" && <RunTable runs={runsFor(["feature_processing", "crop_formula_processing", "sentinel2_history_backfill"])} />}

          {feTab === "profiles" && (
            <div className="space-y-4">
              <Button onClick={() => { setNewProfile((v) => !v); setEditingProfile(null); }} className="rounded-xl bg-emerald-600 text-white"><Plus className="mr-2 h-4 w-4" />New crop profile</Button>
              {newProfile && <ProfileEditor onSaved={() => { setNewProfile(false); load(); }} />}
              <div className="grid gap-3 lg:grid-cols-3">
                {profiles.map((profile) => (
                  <div key={profile.profile_id} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                    <div className="flex items-start justify-between">
                      <div><p className="font-bold text-slate-800">{profile.crop_name}</p><p className="text-xs text-slate-500">{profile.crop_code} · {profile.profile_version}</p></div>
                      <span className={`rounded-full px-2 py-1 text-[10px] font-bold ${profile.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{profile.status}</span>
                    </div>
                    <p className="mt-3 text-xs text-slate-500">History: min {profile.minimum_history_days}d · preferred {profile.preferred_history_days}d</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" onClick={() => { setEditingProfile(profile); setNewProfile(false); }}>Edit/View</Button>
                      {profile.status === "draft" && (
                        <Button size="sm" variant="outline" onClick={async () => {
                          const src = window.prompt("Copy the 10 formulas from which crop code? (coconut / kala_jeera / mango)", "kala_jeera");
                          if (!src) return;
                          try { const r = await seedFormulasIntoProfile(profile.profile_id, { source_crop_code: src.trim() }); setError(""); window.alert(`Seeded ${r.seeded} formula draft(s). Publish them, then publish the profile.`); load(); }
                          catch (err) { setError(err?.message || "Seed failed."); }
                        }}>Seed formulas</Button>
                      )}
                      {profile.status === "draft" && (
                        <Button size="sm" variant="outline" onClick={async () => {
                          try {
                            const r = await publishAllFormulasForProfile(profile.profile_id);
                            setError("");
                            window.alert(`Published ${r.published_count} formula(s).${r.errors?.length ? `\nFailed: ${r.errors.map((e) => `${e.prediction_key} (${e.error})`).join("; ")}` : ""}`);
                            load();
                          } catch (err) { setError(err?.message || "Publish-all failed."); }
                        }}>Publish all formulas</Button>
                      )}
                      {profile.status === "draft" && (
                        <Button size="sm" onClick={async () => {
                          try { await publishCropProfile(profile.profile_id); setError(""); load(); }
                          catch (err) { setError(err?.message || "Publish failed."); }
                        }} className="bg-emerald-600 text-white">Publish profile</Button>
                      )}
                      <Button size="sm" variant="outline" onClick={async () => {
                        const v = window.prompt("New profile version", `${profile.crop_code}_v2`);
                        if (!v) return;
                        try { await cloneCropProfile(profile.profile_id, v.trim()); setError(""); load(); }
                        catch (err) { setError(err?.message || "Clone failed."); }
                      }}>Clone version</Button>
                      {profile.status === "draft" && (
                        <Button size="sm" variant="outline" className="text-rose-600" onClick={async () => {
                          if (!window.confirm(`Delete draft profile "${profile.crop_name}" (${profile.profile_version}) and its draft formulas?`)) return;
                          try { await deleteCropProfile(profile.profile_id); setError(""); load(); }
                          catch (err) { setError(err?.message || "Delete failed."); }
                        }}>Delete draft</Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {editingProfile && <ProfileEditor profile={editingProfile} onSaved={() => { setEditingProfile(null); load(); }} />}
              <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4">
                <div className="mb-3 flex items-center gap-2 font-semibold text-violet-900"><Sprout className="h-4 w-4" />Clone an existing crop into a future crop</div>
                <div className="grid gap-2 md:grid-cols-5">
                  <select className="h-10 rounded-md border bg-white px-2 text-sm" value={cloneCrop.source_crop_code} onChange={(e) => setCloneCrop((p) => ({ ...p, source_crop_code: e.target.value }))}>
                    {activeProfiles.map((p) => <option key={p.crop_code} value={p.crop_code}>{p.crop_name}</option>)}
                  </select>
                  <Input placeholder="target_crop_code" value={cloneCrop.target_crop_code} onChange={(e) => setCloneCrop((p) => ({ ...p, target_crop_code: e.target.value }))} />
                  <Input placeholder="Target crop name" value={cloneCrop.target_crop_name} onChange={(e) => setCloneCrop((p) => ({ ...p, target_crop_name: e.target.value }))} />
                  <Input placeholder="profile version" value={cloneCrop.target_profile_version} onChange={(e) => setCloneCrop((p) => ({ ...p, target_profile_version: e.target.value }))} />
                  <Button onClick={async () => { try { await cloneCropConfiguration(cloneCrop); await load(); } catch (err) { setError(err?.message); } }} className="bg-violet-600 text-white">Clone as drafts</Button>
                </div>
                <p className="mt-2 text-xs text-violet-700">Copies config only. Review weights, windows, soil ranges and thresholds, publish the formula drafts (staged while the profile is a draft), then publish the crop profile last to activate the matching formula set together.</p>
              </div>
            </div>
          )}

          {feTab === "formulas" && (
            <div className="space-y-4">
              <Button onClick={() => { setNewFormula((v) => !v); setEditingFormula(null); }} className="rounded-xl bg-blue-600 text-white"><Plus className="mr-2 h-4 w-4" />New formula</Button>
              {newFormula && <FormulaEditor components={components} onSaved={() => { setNewFormula(false); load(); }} />}
              <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50"><tr>{["Crop", "Prediction", "Version", "Direction", "Order", "Status", "Actions"].map((h) => <th key={h} className="px-3 py-2 text-left text-slate-400">{h}</th>)}</tr></thead>
                  <tbody>
                    {formulas.map((formula) => (
                      <tr key={formula.formula_id} className="border-t">
                        <td className="px-3 py-2 font-semibold">{formula.crop_code}</td>
                        <td className="px-3 py-2">{formula.display_name}<div className="font-mono text-[10px] text-slate-400">{formula.prediction_key}</div></td>
                        <td className="px-3 py-2 font-mono">{formula.formula_version}</td>
                        <td className="px-3 py-2">{formula.score_direction}</td>
                        <td className="px-3 py-2">{formula.execution_order}</td>
                        <td className="px-3 py-2">{formula.status}{formula.is_active ? " · active" : ""}</td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-1">
                            <Button size="sm" variant="outline" onClick={() => { setEditingFormula(formula); setNewFormula(false); }}>Edit/View</Button>
                            {formula.status === "draft" && (
                              <Button size="sm" onClick={async () => {
                                try { await publishFormula(formula.formula_id); setError(""); load(); }
                                catch (err) { setError(err?.message || "Publish failed."); }
                              }} className="bg-blue-600 text-white">Publish</Button>
                            )}
                            <Button size="sm" variant="outline" onClick={async () => {
                              const v = window.prompt("New formula version", `${formula.prediction_key}_${formula.crop_code}_v2`);
                              if (!v) return;
                              try { await cloneFormula(formula.formula_id, v.trim()); setError(""); load(); }
                              catch (err) { setError(err?.message || "Clone failed."); }
                            }}>Clone</Button>
                            {formula.status === "draft" && (
                              <Button size="sm" variant="outline" className="text-rose-600" onClick={async () => {
                                if (!window.confirm(`Delete draft formula ${formula.formula_version}?`)) return;
                                try { await deleteFormula(formula.formula_id); setError(""); load(); }
                                catch (err) { setError(err?.message || "Delete failed."); }
                              }}>Delete</Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {editingFormula && <FormulaEditor formula={editingFormula} components={components} onSaved={() => { setEditingFormula(null); load(); }} />}
            </div>
          )}

          {feTab === "components" && (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {components.map((component) => (
                <div key={component.component_key} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div><p className="font-semibold text-slate-800">{component.display_name}</p><code className="text-[10px] text-slate-400">{component.component_key}</code></div>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px]">{component.output_direction}</span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-600">{component.description}</p>
                  <p className="mt-2 text-[10px] text-slate-400">Impl: {component.implementation_version}</p>
                </div>
              ))}
            </div>
          )}

          {feTab === "content" && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4 text-xs text-amber-900">
                <p className="font-semibold">Farmer-facing metric content</p>
                <p className="mt-1">Edit the signal meaning, score-range labels, status sentences, and field-summary wording here. Calculation thresholds remain controlled by the published formula registry. Changes are draft-first and become visible to farmers only after publishing.</p>
              </div>
              <div className="grid gap-3 lg:grid-cols-2">
                {metricContent.map((content) => (
                  <div key={content.content_id} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div><p className="font-bold text-slate-800">{content.display_name}</p><p className="font-mono text-[10px] text-slate-400">{content.crop_code} · {content.metric_key} · {content.content_version}</p></div>
                      <span className={`rounded-full px-2 py-1 text-[10px] font-bold ${content.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{content.status}{content.is_active ? " · active" : ""}</span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs text-slate-600">{content.signal_meaning}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" onClick={() => setEditingContent(content)}>Edit/View</Button>
                      {content.status === "draft" && <Button size="sm" onClick={async () => { try { await publishMetricContent(content.content_id); await load(); } catch (err) { setError(err?.message || "Publish failed."); } }} className="bg-amber-600 text-white">Publish</Button>}
                      {content.status !== "draft" && <Button size="sm" variant="outline" onClick={async () => { const version = window.prompt("New content version", `${content.metric_key}_v2`); if (!version) return; try { await cloneMetricContent(content.content_id, version.trim()); await load(); } catch (err) { setError(err?.message || "Clone failed."); } }}>Clone draft</Button>}
                    </div>
                  </div>
                ))}
              </div>
              {!metricContent.length && <div className="rounded-2xl border border-slate-100 bg-white p-5 text-sm text-slate-500">No content rows are available. Apply migration <code>20260910_01_crop_intelligence_metric_content.sql</code>.</div>}
              {editingContent && <MetricContentEditor content={editingContent} onSaved={() => { setEditingContent(null); load(); }} />}
            </div>
          )}
        </>
      )}

      {/* ---------------- RASTER MANAGEMENT ---------------- */}
      {!loading && domain === "raster" && (
        <div className="space-y-4">
          <ServiceHealthStrip health={{ raster: health.raster, stac: health.stac, lakehouse: health.lakehouse, orchestrator: health.orchestrator }} />
          <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
            <div className="border-b px-4 py-3 font-semibold text-slate-800">Source adapters (STAC/CMR/CDS → raster processor → lakehouse)</div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-400"><tr><th className="px-3 py-2 text-left">Adapter</th><th className="px-3 py-2 text-left">What it measures</th><th className="px-3 py-2 text-left">Table</th><th className="px-3 py-2 text-right">Rows</th><th className="px-3 py-2 text-right">Farms</th><th className="px-3 py-2 text-left">Latest obs</th></tr></thead>
                <tbody>
                  {RASTER_ADAPTERS.map(([key, name, desc, table]) => {
                    const s = sourceByKey[key] || {};
                    return (
                      <tr key={key} className="border-t">
                        <td className="px-3 py-2 font-semibold">{name}</td>
                        <td className="px-3 py-2 text-slate-500">{desc}</td>
                        <td className="px-3 py-2 font-mono text-[10px]">{table}</td>
                        <td className="px-3 py-2 text-right">{s.row_count ?? "--"}</td>
                        <td className="px-3 py-2 text-right">{s.farm_count ?? "--"}</td>
                        <td className="px-3 py-2">{formatDate(s.latest_observation)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-white p-4 text-xs text-slate-600 shadow-sm">
            <p className="font-semibold text-slate-800">Configuration</p>
            <p className="mt-1">Per-adapter parameters (cloud thresholds, provider, collection ids, max scenes, resampling) are set on each ingestion request and in the dataset registry. A no-code editor for adapter defaults is a follow-up — the registry currently lives in <code>raster_processor_service/app/processors/</code> and <code>hot_stream_orchestrator_service/app/environment_schemas.py</code>.</p>
          </div>
          <RunTable runs={runsFor(["environment_refresh", "farm_analysis_materialize", "sentinel2_history_backfill"])} />
        </div>
      )}

      {/* ---------------- FARM REGISTRY ---------------- */}
      {!loading && domain === "farm-registry" && (
        <div className="space-y-4">
          <ServiceHealthStrip health={{ registry: health.registry, profile: health.profile, location: health.location, boundary: health.boundary }} />
          <div className="rounded-2xl border border-slate-100 bg-white p-4 text-sm text-slate-600 shadow-sm">
            <p className="font-semibold text-slate-800">Crop identity for farms</p>
            <p className="mt-1 text-xs">New farms select a crop at registration from the active published crop profiles below. Each farm's <code>crop_code</code> drives its feature profile, temporal windows and formula set.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {activeProfiles.map((p) => <span key={p.crop_code} className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{p.crop_name} · {p.profile_version}</span>)}
              {!activeProfiles.length && <span className="text-xs text-rose-600">No active crop profiles — publish one in the Feature Engine tab.</span>}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-white p-4 text-xs text-slate-600 shadow-sm">
            <p className="font-semibold text-slate-800">Configuration</p>
            <p className="mt-1">H3 resolution, area limits and polygon vertex caps are in <code>shared/config/settings.py</code>. Location master data is managed in the district-boundary service. A no-code editor for these limits is a follow-up.</p>
          </div>
        </div>
      )}

      {/* ---------------- ANALYTICS ---------------- */}
      {!loading && domain === "analytics" && (
        <div className="space-y-4">
          <ServiceHealthStrip health={{ analytics: health.analytics, observability: health.observability }} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryCard label="Engineered feature rows" value={summary.engineered_feature_rows} />
            <SummaryCard label="Calculated predictions" value={summary.calculated_prediction_rows} />
            <SummaryCard label="Grid calculated values" value={summary.grid_calculation_rows} />
            <SummaryCard label="Active formulas" value={summary.active_formulas} detail={`${summary.active_crop_profiles || 0} profiles`} />
          </div>
          <div className="rounded-2xl border border-slate-100 bg-white p-4 text-xs text-slate-600 shadow-sm">
            <p className="font-semibold text-slate-800">Configuration</p>
            <p className="mt-1">Analytics behaviour (usable-scene cloud ceiling, grid size, weighting) is derived from the feature-engine crop profiles and formula registry configured in the Feature Engine tab. Raw Sentinel-2 mosaic/trends thresholds live in <code>analytics_query_service/app/repository.py</code>.</p>
          </div>
          <RunTable runs={runsFor(["feature_processing", "crop_formula_processing"])} />
        </div>
      )}

      {/* ---------------- HOT STREAM ---------------- */}
      {!loading && domain === "hot-stream" && (
        <div className="space-y-4">
          <ServiceHealthStrip health={{ orchestrator: health.orchestrator, raster: health.raster, lakehouse: health.lakehouse, stac: health.stac }} />
          <div className="rounded-2xl border border-slate-100 bg-white p-4 text-xs text-slate-600 shadow-sm">
            <p className="font-semibold text-slate-800">Orchestration endpoints</p>
            <p className="mt-1 text-[11px]">Normal farmer traffic uses <code>POST /v1/hot-stream/farms/&#123;id&#125;/run-latest-analysis</code> and polls <code>GET /v1/hot-stream/farms/&#123;id&#125;/analysis-status</code>. The routes below are operator diagnostics/backfills.</p>
            <ul className="mt-2 list-inside list-disc space-y-1">
              <li><code>POST /v1/hot-stream/farms/&#123;id&#125;/full-refresh</code> — compatibility alias for the canonical full pipeline</li>
              <li><code>POST /v1/hot-stream/farms/&#123;id&#125;/sentinel2/history-backfill</code> — operator backfill for historical Sentinel-2 observations</li>
              <li><code>POST /v1/hot-stream/farms/&#123;id&#125;/environment-refresh</code> — operator dataset-stage retry; Sentinel-2 is included</li>
            </ul>
            <p className="mt-2">Scheduling cadence is operational config; a no-code scheduler UI is a follow-up.</p>
          </div>
          <RunTable runs={runsFor(["farm_latest_analysis", "farm_analysis_materialize", "environment_refresh", "sentinel2_history_backfill"])} />
        </div>
      )}
    </div>
  );
}
