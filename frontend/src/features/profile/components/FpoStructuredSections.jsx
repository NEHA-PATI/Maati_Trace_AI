import { useEffect, useState } from "react";
import { MapPinned, Plus, Sprout, Trash2 } from "lucide-react";
import { profileApi } from "@/features/profile/api/profileApi";
import { useProfileLocations } from "@/features/profile/hooks/useProfileLocations";

const emptyCommodity = { commodity_code: "", variety_code: "", is_primary: false };
const emptyService = { service_code: "", display_name: "", description: "" };
const emptyArea = { geography_level: "DISTRICT", state_name: "", state_code: "", district_name: "", district_code: "", block_name: "", block_code: "", village_code: "", is_primary: false };

function Section({ id, title, icon, children }) {
  const SectionIcon = icon;
  return <section id={id} className="rounded-2xl border border-[#E3E8DE] bg-white p-5 shadow-[0_4px_14px_rgba(43,61,35,0.04)]"><div className="flex items-center gap-3"><SectionIcon className="h-5 w-5 text-[#4B6B3A]" /><h2 className="text-lg font-black text-[#1D2117]">{title}</h2></div>{children}</section>;
}

function Input({ value, onChange, placeholder, type = "text" }) {
  return <input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="w-full rounded-xl border border-[#DCE8D5] bg-[#FBFDF9] px-3 py-2.5 text-sm outline-none focus:border-[#7FA66A]" />;
}

export function FpoStructuredSections({ onReadinessChange }) {
  const [data, setData] = useState({ commodities: [], services: [], service_areas: [] });
  const [readiness, setReadiness] = useState(null);
  const [commodity, setCommodity] = useState(emptyCommodity);
  const [service, setService] = useState(emptyService);
  const [area, setArea] = useState(emptyArea);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState({ state_name: "", district_name: "" });
  const { states, districts, blocks, loading: locationLoading, optionName } = useProfileLocations({ stateName: location.state_name, districtName: location.district_name });

  const load = async () => {
    const [structured, nextReadiness] = await Promise.all([profileApi.getFpoStructuredProfile(), profileApi.getFpoReadiness()]);
    setData(structured);
    setReadiness(nextReadiness);
    onReadinessChange?.(nextReadiness);
  };

  useEffect(() => { load().catch((loadError) => setError(loadError?.message || "Profile sections could not be loaded.")); }, []);

  const run = async (action) => {
    setError(null);
    try { await action(); await load(); } catch (actionError) { setError(actionError?.message || "The profile section could not be saved."); }
  };

  return <div className="space-y-5">
    {error ? <p className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-sm font-semibold text-rose-700">{error}</p> : null}
    <Section id="commodities" title="Commodities" icon={Sprout}>
      <p className="mt-1 text-sm text-slate-500">Use catalogue codes and mark at least one commodity as primary.</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_1fr_auto_auto]"><Input value={commodity.commodity_code} onChange={(value) => setCommodity({ ...commodity, commodity_code: value })} placeholder="Commodity code" /><Input value={commodity.variety_code} onChange={(value) => setCommodity({ ...commodity, variety_code: value })} placeholder="Variety (optional)" /><label className="flex items-center gap-2 px-2 text-sm"><input type="checkbox" checked={commodity.is_primary} onChange={(event) => setCommodity({ ...commodity, is_primary: event.target.checked })} /> Primary</label><button type="button" onClick={() => run(async () => { await profileApi.addFpoCommodity(commodity); setCommodity(emptyCommodity); })} className="inline-flex items-center justify-center gap-1 rounded-xl bg-[#4B6B3A] px-3 py-2 text-sm font-bold text-white"><Plus className="h-4 w-4" />Add</button></div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">{data.commodities.map((item) => <div key={item.profile_commodity_id} className="flex items-center justify-between rounded-xl bg-[#F5F8F2] px-3 py-2 text-sm"><span className="font-bold text-[#33492A]">{item.commodity_code}{item.variety_code ? ` · ${item.variety_code}` : ""}{item.is_primary ? " · Primary" : ""}</span><button type="button" aria-label={`Remove ${item.commodity_code}`} onClick={() => run(() => profileApi.removeFpoCommodity(item.commodity_code))} className="text-rose-600"><Trash2 className="h-4 w-4" /></button></div>)}</div>
    </Section>
    <Section id="services" title="Services provided" icon={Sprout}>
      <p className="mt-1 text-sm text-slate-500">Maintain the services this FPO actively provides to members.</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_1fr_1fr_auto]"><Input value={service.service_code} onChange={(value) => setService({ ...service, service_code: value })} placeholder="Service code" /><Input value={service.display_name} onChange={(value) => setService({ ...service, display_name: value })} placeholder="Display name" /><Input value={service.description} onChange={(value) => setService({ ...service, description: value })} placeholder="Description" /><button type="button" onClick={() => run(async () => { await profileApi.addFpoService(service); setService(emptyService); })} className="inline-flex items-center justify-center gap-1 rounded-xl bg-[#4B6B3A] px-3 py-2 text-sm font-bold text-white"><Plus className="h-4 w-4" />Add</button></div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">{data.services.map((item) => <div key={item.profile_service_id} className="flex items-center justify-between rounded-xl bg-[#F5F8F2] px-3 py-2 text-sm"><span className="font-bold text-[#33492A]">{item.display_name || item.service_code}</span><button type="button" aria-label={`Remove ${item.service_code}`} onClick={() => run(() => profileApi.removeFpoService(item.service_code))} className="text-rose-600"><Trash2 className="h-4 w-4" /></button></div>)}</div>
    </Section>
    <Section id="service-areas" title="Operational service areas" icon={MapPinned}>
      <p className="mt-1 text-sm text-slate-500">Choose locations from the canonical catalogue. Enter the village name because villages are not yet exposed by the location service.</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <select value={area.geography_level} onChange={(event) => setArea({ ...emptyArea, geography_level: event.target.value })} className="rounded-xl border border-[#DCE8D5] bg-[#FBFDF9] px-3 py-2.5 text-sm"><option>STATE</option><option>DISTRICT</option><option>BLOCK</option><option>VILLAGE</option></select>
        <select value={area.state_name} onChange={(event) => { const item = states.find((entry) => optionName(entry) === event.target.value); setLocation({ state_name: event.target.value, district_name: "" }); setArea({ ...area, state_name: event.target.value, state_code: item?.state_code || "", district_name: "", district_code: "", block_name: "", block_code: "" }); }} className="rounded-xl border border-[#DCE8D5] bg-[#FBFDF9] px-3 py-2.5 text-sm"><option value="">Select state</option>{states.map((item) => <option key={item.state_code} value={optionName(item)}>{optionName(item)}</option>)}</select>
        {area.geography_level !== "STATE" ? <select value={area.district_name} disabled={!area.state_name || locationLoading.districts} onChange={(event) => { const item = districts.find((entry) => optionName(entry) === event.target.value); setLocation((current) => ({ ...current, district_name: event.target.value })); setArea({ ...area, district_name: event.target.value, district_code: item?.district_code || "", block_name: "", block_code: "" }); }} className="rounded-xl border border-[#DCE8D5] bg-[#FBFDF9] px-3 py-2.5 text-sm"><option value="">Select district</option>{districts.map((item) => <option key={item.district_code} value={optionName(item)}>{optionName(item)}</option>)}</select> : null}
        {(area.geography_level === "BLOCK" || area.geography_level === "VILLAGE") ? <select value={area.block_name} disabled={!area.district_name || locationLoading.blocks} onChange={(event) => { const item = blocks.find((entry) => optionName(entry) === event.target.value); setArea({ ...area, block_name: event.target.value, block_code: item?.block_code || "" }); }} className="rounded-xl border border-[#DCE8D5] bg-[#FBFDF9] px-3 py-2.5 text-sm"><option value="">Select block</option>{blocks.map((item) => <option key={item.block_code} value={optionName(item)}>{optionName(item)}</option>)}</select> : null}
        {area.geography_level === "VILLAGE" ? <Input value={area.village_code} onChange={(value) => setArea({ ...area, village_code: value })} placeholder="Village name" /> : null}
        <button type="button" disabled={!area.state_code || (area.geography_level !== "STATE" && !area.district_code) || (area.geography_level === "BLOCK" && !area.block_code) || (area.geography_level === "VILLAGE" && (!area.block_code || !area.village_code.trim()))} onClick={() => run(async () => { await profileApi.addFpoServiceArea({ geography_level: area.geography_level, state_code: Number(area.state_code), district_code: area.district_code ? Number(area.district_code) : null, block_code: area.block_code ? Number(area.block_code) : null, village_code: area.village_code || null, is_primary: area.is_primary }); setArea(emptyArea); setLocation({ state_name: "", district_name: "" }); })} className="inline-flex items-center justify-center gap-1 rounded-xl bg-[#4B6B3A] px-3 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"><Plus className="h-4 w-4" />Add area</button>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">{data.service_areas.map((item) => <div key={item.service_area_id} className="flex items-center justify-between rounded-xl bg-[#F5F8F2] px-3 py-2 text-sm"><span className="font-bold text-[#33492A]">{item.geography_level} · {[item.state_name, item.district_name, item.block_name, item.village_code].filter(Boolean).join(" · ")}</span><button type="button" aria-label="Remove service area" onClick={() => run(() => profileApi.removeFpoServiceArea(item.service_area_id))} className="text-rose-600"><Trash2 className="h-4 w-4" /></button></div>)}</div>
    </Section>
    <Section id="review" title="Review and readiness" icon={Sprout}><div className="mt-4 rounded-xl bg-[#F5F8F2] p-4"><p className="text-2xl font-black text-[#33492A]">{readiness?.percentage ?? 0}% ready</p><p className="mt-1 text-sm text-slate-600">{readiness?.ready ? "Ready for FPO-03 verification." : "Resolve the blocking requirements before submission."}</p>{readiness?.blocking_requirements?.length ? <div className="mt-3 flex flex-wrap gap-2">{readiness.blocking_requirements.map((item) => <span key={item.code} className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">{item.code}</span>)}</div> : null}</div></Section>
  </div>;
}
