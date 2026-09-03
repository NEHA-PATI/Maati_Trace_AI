import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, Plus, Play, User } from "lucide-react";

import {
  attachCropToFarm,
  getCrops,
  getFarmCrops,
  startCropCycle,
} from "@/features/crop-observation/api/cropObservationApi";
import CropCard from "@/features/crop-observation/components/CropCard";
import LanguageFirstRun from "@/features/crop-observation/components/LanguageFirstRun";
import LanguageToggle from "@/features/crop-observation/components/LanguageToggle";
import { CropListSkeleton } from "@/features/crop-observation/components/Skeletons";
import { prefetchStageScreen } from "@/features/crop-observation/hooks/useCropScreen";
import { hasStoredCropLocale, useLocale } from "@/features/crop-observation/hooks/useLocale";
import { useMyFarms } from "@/features/crop-observation/hooks/useMyFarms";
import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { useAuth } from "@/features/auth/context/useAuth";

function firstName(name) {
  return String(name || "farmer").trim().split(/\s+/)[0] || "farmer";
}

function todayLabel(locale) {
  return new Date().toLocaleDateString(locale === "or-IN" ? "or-IN" : "en-IN", {
    weekday: "long",
  });
}

export default function MyCropsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [locale, setLocale] = useLocale();
  const [languageReady, setLanguageReady] = useState(() => hasStoredCropLocale());
  const { farms, loading: farmsLoading, error: farmsError } = useMyFarms();
  const [farmId, setFarmId] = useState("");
  const [crops, setCrops] = useState([]);
  const [farmCropByCode, setFarmCropByCode] = useState(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyCropCode, setBusyCropCode] = useState("");

  const farmerName = firstName(user?.full_name || user?.name);
  const attachedCrops = useMemo(
    () => crops.filter((crop) => farmCropByCode.has(crop.crop_code)),
    [crops, farmCropByCode],
  );
  const availableCrops = attachedCrops.length ? attachedCrops : crops;

  useEffect(() => {
    if (!farmId && farms.length > 0) setFarmId(farms[0].farm_id);
  }, [farms, farmId]);

  useEffect(() => {
    if (!farmId || !languageReady) {
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
        if (!cancelled) setError(err?.message || "Could not load crops.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [farmId, farmsLoading, languageReady, locale]);

  const handleSelectCrop = useCallback(
    async (crop) => {
      setBusyCropCode(crop.crop_code);
      setError("");
      try {
        const existing = farmCropByCode.get(crop.crop_code);
        const farmCrop = existing || (await attachCropToFarm(farmId, { crop_code: crop.crop_code }));
        if (!existing) {
          setFarmCropByCode((prev) => new Map(prev).set(crop.crop_code, farmCrop));
        }
        const cycle = await startCropCycle(farmCrop.farm_crop_id, {});
        prefetchStageScreen(cycle.crop_cycle_id, cycle.current_stage_code, locale);
        navigate(`/my-crops/${farmId}/${cycle.crop_cycle_id}/${cycle.current_stage_code}`);
      } catch (err) {
        setError(
          err?.code === "CROP_CONFIGURATION_MISSING"
            ? `${crop.name} isn't set up for daily updates yet.`
            : err?.message || "Could not open this crop.",
        );
      } finally {
        setBusyCropCode("");
      }
    },
    [farmId, farmCropByCode, locale, navigate],
  );

  if (!languageReady) {
    return (
      <LanguageFirstRun
        locale={locale}
        setLocale={setLocale}
        onContinue={() => {
          setLocale(locale);
          setLanguageReady(true);
        }}
      />
    );
  }

  return (
    <div className="mx-auto min-h-[calc(100vh-4rem)] w-full max-w-[480px] bg-white px-5 pb-[calc(92px+env(safe-area-inset-bottom))] pt-3">
      <div className="mb-3 flex justify-end">
        <LanguageToggle locale={locale} setLocale={setLocale} />
      </div>

      <section className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[21px] font-black leading-tight text-[#1D2117]">Hello, {farmerName}</h1>
          <p className="mt-0.5 text-sm font-medium text-[#5B6055]">Today, {todayLabel(locale)}</p>
        </div>
        <div className="grid h-12 w-12 place-items-center rounded-full bg-[#E7EEE1] text-sm font-black text-[#33492A]">
          {farmerName[0]?.toUpperCase() || <User className="h-5 w-5" />}
        </div>
      </section>

      {availableCrops.length ? (
        <div className="mt-4 flex gap-3 rounded-2xl border border-[#ECD6A8] bg-[#FFF2D9] p-3">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-[#B36B00]" />
          <div>
            <p className="text-sm font-black text-[#1D2117]">Today's update is pending for {availableCrops[0].name}</p>
            <p className="mt-0.5 text-sm font-medium text-[#5B6055]">It only takes 1 minute</p>
          </div>
        </div>
      ) : null}

      {farms.length > 1 ? (
        <select
          value={farmId}
          onChange={(event) => setFarmId(event.target.value)}
          className="mt-4 h-11 w-full rounded-xl border border-[#E9E7DC] bg-white px-3 text-sm font-semibold text-[#1D2117]"
        >
          {farms.map((farm) => (
            <option key={farm.farm_id} value={farm.farm_id}>
              {farm.farm_name}
            </option>
          ))}
        </select>
      ) : null}

      <section className="mt-6">
        <p className="mb-3 text-sm font-black text-[#1D2117]">My crops</p>

        {farmsError ? <p className="text-sm text-rose-600">{farmsError}</p> : null}
        {!farmsLoading && !farmsError && farms.length === 0 ? (
          <p className="text-base font-medium text-[#5B6055]">{primary(STRINGS.noFarm, locale)}</p>
        ) : null}
        {error ? <p className="mb-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

        {loading || farmsLoading ? (
          <CropListSkeleton />
        ) : (
          <div className="space-y-3">
            {availableCrops.map((crop) => (
              <CropCard
                key={crop.crop_code}
                crop={crop}
                locale={locale}
                attached={farmCropByCode.has(crop.crop_code)}
                disabled={busyCropCode === crop.crop_code}
                onSelect={handleSelectCrop}
              />
            ))}
            <button
              type="button"
              onClick={() => {
                const next = crops.find((crop) => !farmCropByCode.has(crop.crop_code)) || crops[0];
                if (next) handleSelectCrop(next);
              }}
              className="flex min-h-[60px] w-full items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[#C9D8BD] bg-white text-[15px] font-black text-[#33492A] active:scale-[0.99]"
            >
              <Plus className="h-5 w-5" />
              Add a new crop
            </button>
          </div>
        )}
      </section>

      <section className="mt-6">
        <p className="mb-3 text-sm font-black text-[#1D2117]">Stories from other farmers</p>
        <div className="flex gap-3 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {["Fertilizer timing", "Coconut care", "Harvest tips"].map((title, index) => (
            <div key={title} className="w-[150px] shrink-0">
              <div
                className={`grid h-[100px] place-items-center rounded-[14px] ${
                  index === 1
                    ? "bg-[linear-gradient(150deg,#B7D09E,#6F965D)]"
                    : "bg-[linear-gradient(150deg,#DDBD8B,#9B6B3F)]"
                }`}
              >
                <span className="grid h-9 w-9 place-items-center rounded-full bg-white text-[#4B6B3A]">
                  <Play className="h-4 w-4 fill-current" />
                </span>
              </div>
              <p className="mt-2 truncate text-xs font-black text-[#1D2117]">{title}</p>
              <p className="truncate text-[11px] font-medium text-[#5B6055]">Farmer story</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
