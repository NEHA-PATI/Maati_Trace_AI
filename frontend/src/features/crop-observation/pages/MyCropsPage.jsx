import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, Plus, User } from "lucide-react";

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
import { useLocale } from "@/features/crop-observation/hooks/useLocale";
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
    <div className="min-h-[calc(100vh-4rem)] bg-[#F6F7F2] pb-[calc(92px+env(safe-area-inset-bottom))]">
      <div className="mx-auto w-full max-w-[1320px] px-4 py-4 sm:px-6 lg:px-8 lg:py-7">
        <header className="flex items-start justify-between gap-4 rounded-[22px] border border-[#E3E8DE] bg-white p-4 shadow-sm sm:p-5">
          <div className="min-w-0">
            <p className="text-sm font-bold text-[#4B6B3A]">{primary(STRINGS.myCrop, locale)}</p>
            <h1 className="mt-1 truncate text-[22px] font-black text-[#1D2117] sm:text-3xl">
              {primary(STRINGS.hello, locale)}{farmerName ? `, ${farmerName}` : ""}
            </h1>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <LanguageToggle locale={locale} setLocale={setLocale} />
            <div className="hidden h-11 w-11 place-items-center rounded-full bg-[#E7EEE1] text-sm font-black text-[#33492A] sm:grid">
              {farmerName?.[0]?.toUpperCase() || <User className="h-5 w-5" />}
            </div>
          </div>
        </header>

        {availableCrops.length ? (
          <div className="mt-4 flex gap-3 rounded-2xl border border-[#ECD6A8] bg-[#FFF2D9] p-3 sm:max-w-[680px]">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-[#B36B00]" />
            <div>
              <p className="text-sm font-black text-[#1D2117]">
                {primary(STRINGS.todaysUpdatePending, locale)} — {availableCrops[0].name}
              </p>
              <p className="mt-0.5 text-sm font-medium text-[#5B6055]">
                {primary(STRINGS.takesOneMinute, locale)}
              </p>
            </div>
          </div>
        ) : null}

        <section className="mt-7">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xl font-black text-[#1D2117]">{primary(STRINGS.myCrops, locale)}</p>
              <p className="mt-1 text-sm font-medium text-[#5B6055]">{primary(STRINGS.chooseCrop, locale)}</p>
            </div>
            {farms.length > 1 ? (
              <select
                value={farmId}
                onChange={(event) => setFarmId(event.target.value)}
                className="h-11 min-w-[240px] rounded-xl border border-[#DCE3D7] bg-white px-3 text-sm font-semibold text-[#1D2117]"
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
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
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
                className="flex min-h-[84px] items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[#C9D8BD] bg-white text-[15px] font-black text-[#33492A] active:scale-[0.99]"
              >
                <Plus className="h-5 w-5" />
                {primary(STRINGS.addNewCrop, locale)}
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
