import {
  Building2,
  CheckCircle2,
  Clock3,
  User,
} from "lucide-react";

import { GrowthRing } from "@/features/profile/components/GrowthRing";

function statusCopy(status) {
  return status === "completed"
    ? {
      label: "Completed",
      icon: CheckCircle2,
      tone: "border-emerald-200/60 bg-white text-emerald-800",
    }
    : {
      label: "Pending",
      icon: Clock3,
      tone: "border-amber-200/60 bg-white text-amber-800",
    };
}

export function ProfileHeader({
  user,
  profile,
  profileType,
  completionPercentage,
  onboardingStatus,
}) {
  const isFpo = profileType === "fpo";
  const AvatarIcon = isFpo
    ? Building2
    : User;
  const status =
    statusCopy(onboardingStatus);
  const StatusIcon = status.icon;

  const title = isFpo
    ? profile?.fpo_name
      || "Your FPO profile"
    : profile?.full_name
      || user?.full_name
      || "Your profile";

  const subtitle = isFpo
    ? profile?.contact_email
      || user?.email
    : user?.email;

  return (
    <div className="mt-fade-up overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)]">
      <div className="relative h-40 overflow-hidden bg-[linear-gradient(135deg,#12331f_0%,#1e5c3f_45%,#6b7f34_100%)] md:h-36">
        <div
          className="absolute inset-0 opacity-[0.16] [background-image:radial-gradient(rgba(255,255,255,0.9)_1px,transparent_1px)] [background-size:22px_22px]"
          aria-hidden="true"
        />
        <div
          className="mt-drift absolute -right-14 -top-20 h-56 w-56 rounded-full bg-lime-200/20 blur-2xl"
          aria-hidden="true"
        />
        <div
          className="absolute -left-10 bottom-[-4rem] h-40 w-40 rounded-full bg-amber-300/10 blur-2xl"
          aria-hidden="true"
        />

        <div className="absolute right-6 top-6 hidden md:block">
          <div
            className="mt-scale-in"
            style={{ "--mt-d": "160ms" }}
          >
            <GrowthRing
              value={completionPercentage}
            />
          </div>
        </div>
      </div>
      <div className="px-6 pb-6">
        <div className="-mt-12 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div className="flex items-end gap-4">
            <div className="mt-scale-in flex h-20 w-20 shrink-0 items-center justify-center rounded-full border-4 border-white bg-[radial-gradient(circle_at_30%_20%,#eef4ea,#dfe9dc)] shadow-lg">
              <AvatarIcon className="h-9 w-9 text-[color:var(--mt-forest)]" />
            </div>
            <div className="pb-1">
              <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.28em] text-[color:var(--mt-harvest)]">
                Profile settings
              </p>
              <h1 className="mt-font-display mt-1 text-[1.9rem] font-semibold leading-[1.1] tracking-tight text-slate-950">
                {title}
              </h1>
              <p className="mt-1.5 text-sm text-slate-600">
                {subtitle}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 md:hidden">
              <div className="relative">
                <GrowthRing
                  value={completionPercentage}
                />
              </div>
            </div>
            <div className="hidden rounded-2xl border border-slate-200 bg-white px-4 py-3 md:block">
              <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                Completion
              </p>
              <p className="mt-font-display mt-1 text-xl font-semibold text-slate-950">
                {completionPercentage}%
              </p>
            </div>
            <div className={`inline-flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-bold shadow-sm transition-transform duration-300 hover:-translate-y-0.5 ${status.tone}`}>
              <StatusIcon className="h-4 w-4" />
              {status.label}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
