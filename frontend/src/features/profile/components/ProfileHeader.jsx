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
      className="relative overflow-hidden rounded-[2rem] border border-emerald-100 bg-white/70 shadow-[0_18px_50px_rgba(15,23,42,0.06)] backdrop-blur-xl"
    >
      <div
        className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.12),transparent_45%),radial-gradient(circle_at_85%_80%,rgba(20,184,166,0.1),transparent_45%)]"
        aria-hidden="true"
      />
      <div
        className="mt-drift absolute -right-10 -top-10 h-48 w-48 rounded-full bg-emerald-200/25 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="absolute -bottom-16 -left-12 h-40 w-40 rounded-full bg-teal-200/20 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="absolute inset-0 opacity-[0.04] [background-image:radial-gradient(#059669_1px,transparent_1px)] [background-size:20px_20px]"
        aria-hidden="true"
      />

      <div className="relative p-6">
        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
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
                className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 shadow-[0_8px_24px_rgba(16,185,129,0.35)]"
              >
                <AvatarIcon className="h-8 w-8 text-white" />
              </Motion.div>
            </div>
            <div>
              <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.28em] text-emerald-600">
                Profile settings
              </p>
              <h1 className="mt-font-display text-2xl font-semibold leading-tight text-slate-900">
                {title}
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                {subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <GrowthRing
              value={completionPercentage}
            />
            <div
              className={`flex items-center gap-2 rounded-2xl border px-4 py-2.5 ${
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
