import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Check, History, Loader2 } from "lucide-react";

import Bilingual from "@/features/crop-observation/components/Bilingual";
import CropStatusSelector from "@/features/crop-observation/components/CropStatusSelector";
import MobileScreen from "@/features/crop-observation/components/MobileScreen";
import PracticeSheet from "@/features/crop-observation/components/PracticeSheet";
import { StageScreenSkeleton } from "@/features/crop-observation/components/Skeletons";
import StageTabs from "@/features/crop-observation/components/StageTabs";
import { useCropScreen } from "@/features/crop-observation/hooks/useCropScreen";
import { useLocale } from "@/features/crop-observation/hooks/useLocale";
import { PRACTICE_META, STRINGS, humanizeCode, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

function newClientEntryId() {
  return crypto.randomUUID ? crypto.randomUUID() : `client-${Date.now()}-${Math.random()}`;
}

export default function CropStagePage() {
  const { farmId, cropCycleId, stageCode } = useParams();
  const navigate = useNavigate();
  const [locale] = useLocale();
  const { screen, loading, error, statusSave, setStatus, reload } = useCropScreen(cropCycleId, stageCode, locale);
  const [activePractice, setActivePractice] = useState(null);

  const goHistory = () => navigate(`/my-crops/${farmId}/${cropCycleId}/history`);

  if (loading && !screen) {
    return (
      <MobileScreen onBack={() => navigate("/my-crops")} title=" ">
        <StageScreenSkeleton />
      </MobileScreen>
    );
  }
  if (error && !screen) {
    return (
      <MobileScreen onBack={() => navigate("/my-crops")}>
        <p className="rounded-xl bg-rose-50 px-3 py-3 text-center text-sm text-rose-700">{error}</p>
      </MobileScreen>
    );
  }
  if (!screen) return null;

  const currentStatus = screen.today.observation?.crop_status || null;
  const todayAnswersByPractice = new Map(
    (screen.today.observation?.practices || []).map((p) => [p.practice_code, p.answers]),
  );
  const todayLabel = new Date(screen.today.date).toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });

  return (
    <MobileScreen
      onBack={() => navigate("/my-crops")}
      title={screen.crop.name}
      subtitle={screen.crop.secondary_name}
      right={
        <button
          type="button"
          onClick={goHistory}
          aria-label="History"
          className="grid h-10 w-10 place-items-center rounded-full text-slate-600 active:bg-slate-100"
        >
          <History className="h-5 w-5" />
        </button>
      }
      contentClassName="px-0 pt-0"
    >
      <StageTabs
        tabs={screen.stage_tabs}
        onSelect={(code) => navigate(`/my-crops/${farmId}/${cropCycleId}/${code}`, { replace: true })}
      />

      <div className="space-y-6 px-4">
        <div className="rounded-2xl bg-white p-4 shadow-sm">
          <Bilingual
            as="div"
            className="text-xl font-black text-slate-950"
            primaryText={screen.stage.name}
            secondaryText={screen.stage.secondary_name}
            secondaryClassName="text-sm"
          />
          <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
            {primary(STRINGS.today, locale)} • {todayLabel}
          </div>
        </div>

        <section>
          <Bilingual
            as="p"
            className="mb-2.5 text-sm font-semibold text-slate-800"
            pair={STRINGS.howIsCrop}
            locale={locale}
          />
          <CropStatusSelector
            options={screen.crop_status_options}
            value={currentStatus}
            pending={statusSave === "saving" ? currentStatus : null}
            onChange={(code) => setStatus(code, newClientEntryId())}
            locale={locale}
          />
          <SaveHint state={statusSave} locale={locale} />
        </section>

        {screen.practices.length > 0 ? (
          <section>
            <Bilingual
              as="p"
              className="mb-2.5 text-sm font-semibold text-slate-800"
              pair={STRINGS.todaysActivities}
              locale={locale}
            />
            <div className="grid grid-cols-2 gap-3">
              {screen.practices.map((practice) => {
                const meta = PRACTICE_META[practice.practice_code];
                const logged = todayAnswersByPractice.has(practice.practice_code);
                return (
                  <button
                    key={practice.practice_code}
                    type="button"
                    onClick={() => setActivePractice(practice)}
                    disabled={practice.fields.length === 0}
                    className={cn(
                      "relative flex min-h-[96px] flex-col items-center justify-center gap-1 rounded-2xl border bg-white py-4 text-center shadow-sm transition active:scale-[0.98] disabled:opacity-40",
                      logged ? "border-emerald-300" : "border-slate-200",
                    )}
                  >
                    {logged ? (
                      <span className="absolute right-2 top-2 grid h-5 w-5 place-items-center rounded-full bg-emerald-100 text-emerald-600">
                        <Check className="h-3.5 w-3.5" />
                      </span>
                    ) : null}
                    <span className="text-2xl">{meta?.icon || "📋"}</span>
                    <Bilingual
                      as="span"
                      className="text-sm font-semibold text-slate-800"
                      primaryText={practice.name}
                      secondaryText={meta?.en && meta.en !== practice.name ? meta.en : humanizeCode(practice.practice_code)}
                      secondaryClassName="text-[11px]"
                    />
                  </button>
                );
              })}
            </div>
          </section>
        ) : null}
      </div>

      {activePractice ? (
        <PracticeSheet
          practice={activePractice}
          cropCycleId={cropCycleId}
          stageCode={stageCode}
          locale={locale}
          initialAnswers={todayAnswersByPractice.get(activePractice.practice_code) || {}}
          onClose={() => setActivePractice(null)}
          onSaved={() => {
            setActivePractice(null);
            reload({ revalidateOnly: true });
          }}
        />
      ) : null}
    </MobileScreen>
  );
}

function SaveHint({ state, locale }) {
  if (state === "saving") {
    return (
      <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
        <Loader2 className="h-3.5 w-3.5 animate-spin" /> {primary(STRINGS.saving, locale)}
      </p>
    );
  }
  if (state === "saved") {
    return (
      <p className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-emerald-600">
        <Check className="h-3.5 w-3.5" /> {primary(STRINGS.saved, locale)}
      </p>
    );
  }
  if (state === "error") {
    return <p className="mt-2 text-xs text-rose-600">{primary(STRINGS.couldNotSave, locale)}</p>;
  }
  return null;
}
