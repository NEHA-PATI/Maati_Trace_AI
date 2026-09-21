import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Check, ChevronRight, History, Loader2 } from "lucide-react";

import Bilingual from "@/features/crop-observation/components/Bilingual";
import CropStatusSelector from "@/features/crop-observation/components/CropStatusSelector";
import DailyMediaCapture from "@/features/crop-observation/components/DailyMediaCapture";
import HistoryTimeline from "@/features/crop-observation/components/HistoryTimeline";
import LanguageToggle from "@/features/crop-observation/components/LanguageToggle";
import MobileScreen from "@/features/crop-observation/components/MobileScreen";
import PracticeSheet from "@/features/crop-observation/components/PracticeSheet";
import StageInstructionAudio from "@/features/crop-observation/components/StageInstructionAudio";
import StageTabs from "@/features/crop-observation/components/StageTabs";
import { StageScreenSkeleton } from "@/features/crop-observation/components/Skeletons";
import { systemMediaUrl } from "@/features/crop-observation/api/cropObservationApi";
import { iconForPractice } from "@/features/crop-observation/components/fieldIcons";
import { useCropScreen } from "@/features/crop-observation/hooks/useCropScreen";
import { useLocale } from "@/features/crop-observation/hooks/useLocale";
import { PRACTICE_META, STRINGS, primary } from "@/features/crop-observation/i18n";
import { cn } from "@/lib/utils";

function newClientEntryId() {
  return crypto.randomUUID ? crypto.randomUUID() : `client-${Date.now()}-${Math.random()}`;
}

export default function CropStagePage() {
  const { farmId, cropCycleId, stageCode } = useParams();
  const navigate = useNavigate();
  const [locale, setLocale] = useLocale();
  const { screen, loading, error, statusSave, setStatus, reload } = useCropScreen(cropCycleId, stageCode, locale);
  const [activePractice, setActivePractice] = useState(null);
  const goHistory = () => navigate(`/my-crops/${farmId}/${cropCycleId}/history`);

  if (loading && !screen) {
    return <MobileScreen onBack={() => navigate("/my-crops")} title=" "><div className="p-4"><StageScreenSkeleton /></div></MobileScreen>;
  }
  if (error && !screen) {
    return <MobileScreen onBack={() => navigate("/my-crops")}><p className="m-4 rounded-xl bg-rose-50 px-3 py-3 text-center text-sm text-rose-700">{primary(STRINGS.couldNotLoad, locale)}</p></MobileScreen>;
  }
  if (!screen) return null;

  const currentStatus = screen.today.observation?.crop_status || null;
  const todayAnswersByPractice = new Map((screen.today.observation?.practices || []).map((p) => [p.practice_code, p]));
  const todayLabel = new Date(screen.today.date).toLocaleDateString(locale === "or-IN" ? "or-IN" : "en-IN", { weekday: "short", day: "numeric", month: "short" });

  const history = screen.recent_history?.length ? (
    <section className="rounded-[20px] border border-[#E3E8DE] bg-[#FBFCF8] p-4">
      <p className="mb-3 text-base font-bold text-[#1D2117]">{primary(STRINGS.recentRecords, locale)}</p>
      <HistoryTimeline items={screen.recent_history} locale={locale} />
    </section>
  ) : null;

  return (
    <MobileScreen
      onBack={() => navigate("/my-crops")}
      title={screen.crop.name}
      right={(
        <>
          <LanguageToggle locale={locale} setLocale={setLocale} />
          <button type="button" onClick={goHistory} aria-label={primary(STRINGS.history, locale)} className="grid h-12 w-12 place-items-center rounded-[14px] border border-[#E9E7DC] bg-[#F7F8F3] text-[#33492A] active:scale-[0.98]">
            <History className="h-5 w-5" />
          </button>
        </>
      )}
      contentClassName="px-0 pt-0"
    >
      <StageTabs tabs={screen.stage_tabs} onSelect={(code) => navigate(`/my-crops/${farmId}/${cropCycleId}/${code}`, { replace: true })} />

      <div className="grid gap-6 px-4 py-4 sm:px-5 lg:grid-cols-[minmax(0,1fr)_340px] lg:px-6">
        <div className="space-y-5">
          <div className="relative min-h-[190px] overflow-hidden rounded-[22px] bg-[#4B6B3A] p-5 text-white shadow-sm lg:min-h-[260px]">
            {screen.stage.image_url ? (
              <img src={systemMediaUrl(screen.stage.image_url)} alt="" className="absolute inset-0 h-full w-full object-cover opacity-45" loading="eager" />
            ) : <div className="absolute inset-0 bg-[linear-gradient(145deg,#7FA66A,#4B6B3A)]" />}
            <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(29,33,23,0.08),rgba(29,33,23,0.65))]" />
            <div className="absolute right-4 top-4"><StageInstructionAudio src={systemMediaUrl(screen.stage.instruction_audio_url)} locale={locale} /></div>
            <div className="relative flex min-h-[150px] flex-col justify-end lg:min-h-[220px]">
              <Bilingual as="div" className="mt-5 text-[22px] font-black leading-tight lg:text-3xl" primaryText={screen.stage.name} />
              {screen.stage.short_description ? <p className="mt-2 max-w-[720px] text-sm font-medium leading-6 text-white/95">{screen.stage.short_description}</p> : null}
            </div>
          </div>

          <section className="rounded-[20px] border border-[#E3E8DE] bg-white p-4 sm:p-5">
            <div className="mb-3 flex items-end justify-between gap-3">
              <Bilingual as="p" className="text-base font-bold text-[#1D2117] sm:text-lg" pair={STRINGS.howIsCrop} locale={locale} />
              <span className="shrink-0 text-xs font-bold text-[#5B6055]">{todayLabel}</span>
            </div>
            <CropStatusSelector options={screen.crop_status_options} value={currentStatus} pending={statusSave === "saving" ? currentStatus : null} onChange={(code) => setStatus(code, newClientEntryId())} locale={locale} />
            <SaveHint state={statusSave} locale={locale} />
            <DailyMediaCapture dailyObservationId={screen.today.observation?.daily_observation_id} locale={locale} />
          </section>

          <div className="lg:hidden">{history}</div>

          {screen.practices.length > 0 ? (
            <section className="rounded-[20px] border border-[#E3E8DE] bg-white p-4 sm:p-5">
              <Bilingual as="p" className="mb-3 text-base font-bold text-[#1D2117] sm:text-lg" pair={STRINGS.todaysActivities} locale={locale} />
              <div className="grid gap-2.5 sm:grid-cols-2">
                {screen.practices.map((practice) => {
                  const PracticeIcon = iconForPractice(practice.practice_code);
                  const meta = PRACTICE_META[practice.practice_code];
                  const logged = todayAnswersByPractice.has(practice.practice_code);
                  return (
                    <button key={practice.practice_code} type="button" onClick={() => setActivePractice(practice)} disabled={practice.fields.length === 0} className={cn("flex min-h-[78px] w-full items-center gap-3 rounded-2xl border bg-[#FBFCF8] px-3 py-3 text-left transition active:scale-[0.99] disabled:opacity-40", logged ? "border-[#AFC99F]" : "border-[#E9E7DC]") }>
                      <span className="grid h-[42px] w-[42px] shrink-0 place-items-center rounded-xl bg-[#E1F1D6] text-[#33492A]"><PracticeIcon className="h-5 w-5" /></span>
                      <span className="min-w-0 flex-1">
                        <Bilingual as="span" className="block truncate text-[15px] font-bold text-[#1D2117]" primaryText={practice.name} />
                        <span className="mt-0.5 block text-xs font-medium text-[#5B6055]">{logged ? primary(STRINGS.loggedToday, locale) : primary(meta, locale) || primary(STRINGS.newUpdate, locale)}</span>
                      </span>
                      {logged ? <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[#2E8B57] text-white"><Check className="h-3.5 w-3.5" /></span> : <ChevronRight className="h-5 w-5 shrink-0 text-[#5B6055]" />}
                    </button>
                  );
                })}
              </div>
            </section>
          ) : null}
        </div>

        <aside className="hidden lg:block"><div className="sticky top-5">{history}</div></aside>
      </div>

      {activePractice ? (
        <PracticeSheet practice={activePractice} cropCycleId={cropCycleId} stageCode={stageCode} locale={locale} practiceObservationId={todayAnswersByPractice.get(activePractice.practice_code)?.practice_observation_id} initialAnswers={todayAnswersByPractice.get(activePractice.practice_code)?.answers || {}} onClose={() => setActivePractice(null)} onSaved={() => { setActivePractice(null); reload({ revalidateOnly: true }); }} />
      ) : null}
    </MobileScreen>
  );
}

function SaveHint({ state, locale }) {
  if (state === "saving") return <p className="mt-2 flex items-center gap-1.5 text-sm font-medium text-[#5B6055]"><Loader2 className="h-3.5 w-3.5 animate-spin" /> {primary(STRINGS.saving, locale)}</p>;
  if (state === "saved") return <p className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-[#2E8B57]"><Check className="h-3.5 w-3.5" /> {primary(STRINGS.saved, locale)}</p>;
  if (state === "error") return <p className="mt-2 text-xs text-rose-600">{primary(STRINGS.couldNotSave, locale)}</p>;
  return null;
}
