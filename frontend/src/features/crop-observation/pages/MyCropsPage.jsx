import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Grid2X2, List, User, Sprout } from "lucide-react";

import {
  attachCropToFarm,
  getCrops,
  getFarmCrops,
  startCropCycle,
} from "@/features/crop-observation/api/cropObservationApi";
import CropCard from "@/features/crop-observation/components/CropCard";
import LanguageToggle from "@/features/crop-observation/components/LanguageToggle";
import { CropListSkeleton } from "@/features/crop-observation/components/Skeletons";
import { prefetchStageScreen } from "@/features/crop-observation/hooks/useCropScreen";
import { hasStoredCropLocale, useLocale } from "@/features/crop-observation/hooks/useLocale";
import { useMyFarms } from "@/features/crop-observation/hooks/useMyFarms";
import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { useAuth } from "@/features/auth/context/useAuth";

function firstName(name) {
  return String(name || "").trim().split(/\s+/)[0] || "";
}

function localizedError(err, locale, fallbackEn, fallbackOr) {
  if (err?.message && !/^Could not/i.test(err.message)) return err.message;
  return locale === "or-IN" ? fallbackOr : fallbackEn;
}

export default function MyCropsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [locale, setLocale] = useLocale();
  const { farms, loading: farmsLoading, error: farmsError } = useMyFarms();
  const [farmId, setFarmId] = useState("");
  const [crops, setCrops] = useState([]);
  const [farmCropByCode, setFarmCropByCode] = useState(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyCropCode, setBusyCropCode] = useState("");
  const [pendingCrop, setPendingCrop] = useState(null);
  const [viewMode, setViewMode] = useState(() => {
    try { return localStorage.getItem("crop_view_mode") || "cards"; } catch { return "cards"; }
  });

  const farmerName = firstName(user?.full_name || user?.name);
  const attachedCrops = useMemo(
    () => crops.filter((crop) => farmCropByCode.has(crop.crop_code)),
    [crops, farmCropByCode],
  );
  const otherCrops = useMemo(
    () => crops.filter((crop) => !farmCropByCode.has(crop.crop_code)),
    [crops, farmCropByCode],
  );

  useEffect(() => {
    if (!hasStoredCropLocale()) navigate("/my-crops/language", { replace: true });
  }, [navigate]);

  function changeViewMode(mode) {
    setViewMode(mode);
    try { localStorage.setItem("crop_view_mode", mode); } catch { /* memory fallback */ }
  }

  useEffect(() => {
    if (!farmId && farms.length > 0) setFarmId(farms[0].farm_id);
  }, [farms, farmId]);

  useEffect(() => {
    if (!farmId) {
      if (!farmsLoading) setLoading(false);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [cropList, farmCrops] = await Promise.all([getCrops(locale), getFarmCrops(farmId)]);
        if (cancelled) return;
        setCrops(cropList.items || []);
        setFarmCropByCode(new Map((farmCrops || []).map((farmCrop) => [farmCrop.crop_code, farmCrop])));
      } catch (err) {
        if (!cancelled) {
          setError(
            localizedError(
              err,
              locale,
              "Could not load crops.",
              "ଫସଲ ତାଲିକା ଖୋଲିହେଲା ନାହିଁ।",
            ),
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [farmId, farmsLoading, locale]);

  const handleSelectCrop = useCallback(
    async (crop) => {
      if (!farmId) return;
      setBusyCropCode(crop.crop_code);
      setError("");
      try {
        const existing = farmCropByCode.get(crop.crop_code);
        const farmCrop = existing || (await attachCropToFarm(farmId, { crop_code: crop.crop_code }));
        if (!existing) setFarmCropByCode((prev) => new Map(prev).set(crop.crop_code, farmCrop));
        const cycle = await startCropCycle(farmCrop.farm_crop_id, {});
        prefetchStageScreen(cycle.crop_cycle_id, cycle.current_stage_code, locale);
        navigate(`/my-crops/${farmId}/${cycle.crop_cycle_id}/${cycle.current_stage_code}`);
      } catch (err) {
        setError(
          localizedError(
            err,
            locale,
            `${crop.name} is not ready for crop updates yet.`,
            `${crop.name} ପାଇଁ ଏବେ ତଥ୍ୟ ଦେବା ବ୍ୟବସ୍ଥା ପ୍ରସ୍ତୁତ ନାହିଁ।`,
          ),
        );
      } finally {
        setBusyCropCode("");
      }
    },
    [farmId, farmCropByCode, locale, navigate],
  );

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#F3F6EF] pb-[calc(92px+env(safe-area-inset-bottom))]">
      <div className="mx-auto w-full max-w-[1600px] px-4 py-4 sm:px-6 lg:px-10 lg:py-7">
        <header className="relative flex items-center justify-between gap-4 overflow-hidden rounded-[26px] border border-[#DCE8D6] bg-[#EAF3E4] p-5 shadow-[0_12px_30px_rgba(43,61,35,0.08)] sm:p-7">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-sm font-bold text-[#426333]"><Sprout className="h-4 w-4" />{primary(STRINGS.myCrop, locale)}</div>
            <h1 className="mt-1 truncate text-[25px] font-black tracking-[-0.03em] text-[#1D2117] sm:text-4xl">
              {primary(STRINGS.hello, locale)}{farmerName ? `, ${farmerName}` : ""}
            </h1>
            <p className="mt-1 hidden text-xs font-medium text-[#687A60] sm:block">Your crop health journey starts here.</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <LanguageToggle locale={locale} setLocale={setLocale} />
            <div className="hidden h-11 w-11 place-items-center rounded-full bg-[#E7EEE1] text-sm font-black text-[#33492A] sm:grid">
              {farmerName?.[0]?.toUpperCase() || <User className="h-5 w-5" />}
            </div>
          </div>
        </header>

        <section className="mt-7">
          <div className="mb-5 flex flex-col gap-4 rounded-2xl border border-[#E0E8DB] bg-white/70 p-4 sm:flex-row sm:items-end sm:justify-between sm:p-5">
            <div>
              <div className="flex items-center gap-2"><p className="text-xl font-black text-[#1D2117]">{primary(STRINGS.myCrops, locale)}</p><span className="rounded-full bg-[#E1F1D6] px-2 py-1 text-[10px] font-black uppercase tracking-wide text-[#426333]">Field view</span></div>
              <p className="mt-1 text-sm font-medium text-[#5B6055]">{primary(STRINGS.chooseCrop, locale)}</p>
            </div>
            <div className="flex items-center justify-center gap-2 rounded-xl bg-[#F3F6EF] p-1 sm:justify-end">
              <button type="button" onClick={() => changeViewMode("cards")} aria-pressed={viewMode === "cards"} className={`inline-flex h-9 items-center gap-1 rounded-lg px-3 text-xs font-bold transition ${viewMode === "cards" ? "bg-white text-[#33492A] shadow-sm" : "text-[#687A60]"}`}><Grid2X2 className="h-3.5 w-3.5" />{primary(STRINGS.cards, locale)}</button>
              <button type="button" onClick={() => changeViewMode("list")} aria-pressed={viewMode === "list"} className={`inline-flex h-9 items-center gap-1 rounded-lg px-3 text-xs font-bold transition ${viewMode === "list" ? "bg-white text-[#33492A] shadow-sm" : "text-[#687A60]"}`}><List className="h-3.5 w-3.5" />{primary(STRINGS.list, locale)}</button>
            </div>
            {farms.length > 1 ? (
              <select
                value={farmId}
                onChange={(event) => setFarmId(event.target.value)}
                className="h-11 min-w-[240px] rounded-xl border border-[#DCE3D7] bg-white px-3 text-sm font-semibold text-[#1D2117] shadow-sm"
              >
                {farms.map((farm) => (
                  <option key={farm.farm_id} value={farm.farm_id}>{farm.farm_name}</option>
                ))}
              </select>
            ) : null}
          </div>

          {farmsError ? <p className="text-sm text-rose-600">{farmsError}</p> : null}
          {!farmsLoading && !farmsError && farms.length === 0 ? (
            <p className="rounded-2xl bg-white p-5 text-base font-medium text-[#5B6055]">
              {primary(STRINGS.noFarm, locale)}
            </p>
          ) : null}
          {error ? <p className="mb-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

          {loading || farmsLoading ? (
            <CropListSkeleton />
          ) : (
            <div className={`grid gap-3 ${viewMode === "cards" ? "md:grid-cols-2 xl:grid-cols-3" : "grid-cols-1 max-w-2xl"}`}>
              {attachedCrops.map((crop) => (
                <CropCard
                  key={crop.crop_code}
                  crop={crop}
                  locale={locale}
                  attached={farmCropByCode.has(crop.crop_code)}
                  disabled={busyCropCode === crop.crop_code}
                  onSelect={handleSelectCrop}
                />
              ))}
              {otherCrops.length ? <div className="col-span-full mt-5 flex items-center gap-3"><p className="text-sm font-black uppercase tracking-[0.08em] text-[#52604D]">{primary(STRINGS.otherCrops, locale)}</p><span className="h-px flex-1 bg-[#DDE5D7]" aria-hidden="true" /></div> : null}
              {otherCrops.map((crop) => (
                <CropCard key={crop.crop_code} crop={crop} locale={locale} attached={false} disabled={busyCropCode === crop.crop_code} onSelect={() => setPendingCrop(crop)} />
              ))}
            </div>
          )}
        </section>
      </div>
      {pendingCrop ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl">
            <p className="text-lg font-black text-[#1D2117]">{primary(STRINGS.addCropConfirm, locale)}: {pendingCrop.name}?</p>
            <div className="mt-4 flex gap-2">
              <button type="button" onClick={() => setPendingCrop(null)} className="h-11 flex-1 rounded-xl border border-[#E9E7DC] font-bold text-[#5B6055]">{primary(STRINGS.cancel, locale)}</button>
              <button type="button" onClick={() => { const crop = pendingCrop; setPendingCrop(null); handleSelectCrop(crop); }} className="h-11 flex-1 rounded-xl bg-[#4B6B3A] font-bold text-white">{primary(STRINGS.addCrop, locale)}</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
