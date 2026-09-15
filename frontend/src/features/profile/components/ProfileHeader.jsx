import { motion as Motion } from "framer-motion";
import {
  BadgeCheck,
  Building2,
  Clock3,
  UserRound,
} from "lucide-react";

import { GrowthRing } from "@/features/profile/components/GrowthRing";

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
    : UserRound;
  const isCompleted =
    onboardingStatus === "completed";
  const StatusIcon = isCompleted
    ? BadgeCheck
    : Clock3;
  const statusLabel = isCompleted
    ? "Completed"
    : "Pending";

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
    <Motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.5,
        ease: [0.16, 1, 0.3, 1],
      }}
      className="relative overflow-hidden rounded-[2rem] border border-emerald-100 bg-white shadow-[0_16px_40px_rgba(15,23,42,0.07)]"
    >
      <div
        className="absolute inset-x-0 top-0 h-1 bg-emerald-500"
        aria-hidden="true"
      />
      <div
        className="absolute right-5 top-5 h-20 w-20 rounded-full bg-emerald-50"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-0 left-0 h-16 w-16 rounded-full bg-emerald-50"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-0"
        aria-hidden="true"
      />

      <div className="relative p-5 sm:p-6">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div className="relative shrink-0">
              <div
                className="absolute inset-0 rounded-2xl bg-emerald-400/30 blur-lg"
                aria-hidden="true"
              />
              <Motion.div
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{
                  delay: 0.15,
                  type: "spring",
                  stiffness: 300,
                  damping: 22,
                }}
                className="relative flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-[1.35rem] bg-emerald-500 shadow-[0_10px_22px_rgba(16,185,129,0.25)]"
              >
                <AvatarIcon className="h-8 w-8 text-white" />
              </Motion.div>
            </div>
            <div>
              <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.25em] text-emerald-700">
                Profile settings
              </p>
              <h1 className="mt-font-display mt-0.5 text-[1.75rem] font-semibold leading-tight text-slate-950">
                {title}
              </h1>
              <p className="mt-1 text-sm text-slate-500/90">
                {subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 border-t border-emerald-900/10 pt-4 md:border-t-0 md:pt-0">
            <GrowthRing
              value={completionPercentage}
            />
            <div
              className={`flex min-h-11 items-center gap-2 rounded-2xl border px-4 py-2.5 shadow-sm ${
                isCompleted
                  ? "border-emerald-100 bg-emerald-50/80"
                  : "border-amber-100 bg-amber-50/80"
              }`}
            >
              <StatusIcon
                className={`h-4 w-4 ${
                  isCompleted
                    ? "text-emerald-600"
                    : "text-amber-600"
                }`}
              />
              <span
                className={`text-sm font-bold ${
                  isCompleted
                    ? "text-emerald-700"
                    : "text-amber-700"
                }`}
              >
                {statusLabel}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Motion.div>
  );
}
