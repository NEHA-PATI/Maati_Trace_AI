import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  attachCropToFarm,
  getCrops,
  getFarmCrops,
  startCropCycle,
} from "@/features/crop-observation/api/cropObservationApi";
import Bilingual from "@/features/crop-observation/components/Bilingual";
import CropCard from "@/features/crop-observation/components/CropCard";
import LanguageToggle from "@/features/crop-observation/components/LanguageToggle";
import MobileScreen from "@/features/crop-observation/components/MobileScreen";
import { CropListSkeleton } from "@/features/crop-observation/components/Skeletons";
import { prefetchStageScreen } from "@/features/crop-observation/hooks/useCropScreen";
import { useLocale } from "@/features/crop-observation/hooks/useLocale";
import { useMyFarms } from "@/features/crop-observation/hooks/useMyFarms";
import { STRINGS, primary } from "@/features/crop-observation/i18n";

export default function MyCropsPage() {
  const navigate = useNavigate();
  const [locale, setLocale] = useLocale();
  const { farms, loading: farmsLoading, error: farmsError } = useMyFarms();
  const [farmId, setFarmId] = useState("");
  const [crops, setCrops] = useState([]);
  const [attachedCodes, setAttachedCodes] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyCropCode, setBusyCropCode] = useState("");

  useEffect(() => {
    if (!farmId && farms.length > 0) setFarmId(farms[0].farm_id);
  }, [farms, farmId]);

  useEffect(() => {
    if (!farmId) return undefined;
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError("");
      try {
        const [cropList, farmCrops] = await Promise.all([getCrops(locale), getFarmCrops(farmId)]);
        if (cancelled) return;
        setCrops(cropList.items || []);
        setAttachedCodes(new Set((farmCrops || []).map((fc) => fc.crop_code)));
      } catch (err) {
        if (!cancelled) setError(err?.message || "Could not load crops.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [farmId, locale]);

  const handleSelectCrop = useCallback(
    async (crop) => {
      setBusyCropCode(crop.crop_code);
      setError("");
      try {
        const farmCrop = await attachCropToFarm(farmId, { crop_code: crop.crop_code });
        const cycle = await startCropCycle(farmCrop.farm_crop_id, {});
        prefetchStageScreen(cycle.crop_cycle_id, cycle.current_stage_code, locale);
        navigate(`/my-crops/${farmId}/${cycle.crop_cycle_id}/${cycle.current_stage_code}`);
      } catch (err) {
        setError(
          err?.code === "CROP_CONFIGURATION_MISSING"
            ? `${crop.name} isn't set up for daily updates yet — check back soon.`
            : err?.message || "Could not open this crop.",
        );
      } finally {
        setBusyCropCode("");
      }
    },
    [farmId, locale, navigate],
  );

  return (
    <MobileScreen
      title={primary(STRINGS.myCrop, locale)}
      subtitle={locale === "or-IN" ? "My Crop" : "ମୋ ଫସଲ"}
      right={<LanguageToggle locale={locale} setLocale={setLocale} />}
    >
      {farms.length > 1 ? (
        <select
          value={farmId}
          onChange={(event) => setFarmId(event.target.value)}
          className="mb-4 h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
        >
          {farms.map((farm) => (
            <option key={farm.farm_id} value={farm.farm_id}>
              {farm.farm_name}
            </option>
          ))}
        </select>
      ) : null}

      <Bilingual
        as="p"
        className="mb-4 text-sm font-semibold text-slate-700"
        pair={STRINGS.chooseCrop}
        locale={locale}
      />

      {farmsError ? <p className="text-sm text-rose-600">{farmsError}</p> : null}
      {!farmsLoading && !farmsError && farms.length === 0 ? (
        <p className="text-sm text-slate-500">{primary(STRINGS.noFarm, locale)}</p>
      ) : null}
      {error ? (
        <p className="mb-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
      ) : null}

      {loading || farmsLoading ? (
        <CropListSkeleton />
      ) : (
        <div className="space-y-3">
          {crops.map((crop) => (
            <CropCard
              key={crop.crop_code}
              crop={crop}
              locale={locale}
              attached={attachedCodes.has(crop.crop_code)}
              disabled={busyCropCode === crop.crop_code}
              onSelect={handleSelectCrop}
            />
          ))}
        </div>
      )}
    </MobileScreen>
  );
}
