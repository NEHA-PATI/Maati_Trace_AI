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
      className="relative overflow-hidden rounded-[1.5rem] border border-[#E3E8DE] bg-white shadow-[0_12px_32px_rgba(43,61,35,0.07)]"
    >
      <div
        className="absolute inset-x-0 top-0 h-1 bg-[#7FA66A]"
        aria-hidden="true"
      />
      <div
        className="absolute right-5 top-5 h-20 w-20 rounded-full bg-[#F0F7EB]"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-0 left-0 h-16 w-16 rounded-full bg-[#F0F7EB]"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-0"
        aria-hidden="true"
      />

      <div className="relative p-4 sm:p-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="relative shrink-0">
              <div
                className="absolute inset-0 rounded-2xl bg-[#AFC99F]/35 blur-lg"
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
                className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-[#4B6B3A] shadow-[0_10px_22px_rgba(75,107,58,0.24)]"
              >
                <AvatarIcon className="h-7 w-7 text-white" />
              </Motion.div>
            </div>
            <div>
              <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.25em] text-[#6E8A5D]">
                Profile settings
              </p>
              <h1 className="mt-font-display mt-0.5 text-[1.75rem] font-semibold leading-tight text-[#1D2117]">
                {title}
              </h1>
              <p className="mt-1 text-sm text-[#687064]">
                {subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 border-t border-[#E3E8DE] pt-4 md:border-t-0 md:pt-0">
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
