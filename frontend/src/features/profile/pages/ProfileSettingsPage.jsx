import {
  useEffect,
  useState,
} from "react";
import { motion as Motion } from "framer-motion";
import {
  Building2,
  Check,
  Download,
  FileText,
  MapPin,
  ShieldCheck,
  Shield,
  Sparkles,
  User,
  Wheat,
} from "lucide-react";

import "@/features/profile/profile-design.css";
import { FarmerProfileForm } from "@/features/profile/components/FarmerProfileForm";
import { FpoProfileForm } from "@/features/profile/components/FpoProfileForm";
import { ProfileHeader } from "@/features/profile/components/ProfileHeader";
import { ProfileNavigation } from "@/features/profile/components/ProfileNavigation";
import {
  ProfileLoadError,
  ProfileLoading,
  UnsupportedProfileRole,
} from "@/features/profile/components/ProfileStates";
import { useProfile } from "@/features/profile/hooks/useProfile";
import {
  downloadProfileJson,
  readableFieldName,
} from "@/features/profile/profileMappers";

const FARMER_NAV = [
  { id: "account", label: "Account", icon: User },
  { id: "identity", label: "Identity", icon: Shield },
  { id: "location", label: "Location", icon: MapPin },
  { id: "role", label: "Role Details", icon: Wheat },
  { id: "consent", label: "Consent", icon: Check },
  { id: "plan", label: "Your Plan", icon: Sparkles },
  { id: "export", label: "Export", icon: Download },
];

const FPO_NAV = [
  { id: "organisation", label: "Organisation", icon: Building2 },
  { id: "contact", label: "Contact", icon: User },
  { id: "location", label: "Location", icon: MapPin },
  { id: "operations", label: "Operations", icon: Wheat },
  { id: "verification", label: "Verification", icon: Shield },
  { id: "plan", label: "Your Plan", icon: Sparkles },
  { id: "export", label: "Export", icon: FileText },
];

function ProfileMissingFields({
  missingFields,
}) {
  if (!missingFields.length) {
    return (
      <Motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3 rounded-[1.25rem] border border-emerald-100 bg-[color:var(--mt-forest-soft)] p-4 text-sm font-semibold text-emerald-900"
      >
        <ShieldCheck className="h-5 w-5 shrink-0 text-[color:var(--mt-forest)]" />
        Required profile fields are complete. The percentage can still
        increase as optional details are filled.
      </Motion.div>
    );
  }

  return (
    <Motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[1.25rem] border border-amber-200 bg-[color:var(--mt-harvest-soft)] p-4 text-sm text-amber-950"
    >
      <p className="mt-font-display font-semibold">
        Required fields still missing
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {missingFields.map((field, index) => (
          <Motion.span
            key={field}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              delay: index * 0.05,
            }}
            className="rounded-full bg-white px-3 py-1 text-xs font-bold text-amber-800 shadow-sm"
          >
            {readableFieldName(field)}
          </Motion.span>
        ))}
      </div>
    </Motion.div>
  );
}

export function ProfileSettingsPage() {
  const {
    user,
    envelope,
    profile,
    profileType,
    onboardingStatus,
    completionPercentage,
    missingFields,
    setupRequired,
    loading,
    error,
    saving,
    exporting,
    savedAt,
    loadProfile,
    saveFarmerProfile,
    saveFpoProfile,
    exportProfile,
  } = useProfile();

  const [activeSection, setActiveSection] =
    useState("account");

  useEffect(() => {
    if (profileType === "fpo") {
      setActiveSection("organisation");
    } else {
      setActiveSection("account");
    }
  }, [profileType]);

  if (loading) {
    return <ProfileLoading />;
  }

  if (error && !envelope) {
    return (
      <ProfileLoadError
        error={error}
        onRetry={loadProfile}
      />
    );
  }

  if (
    profileType !== "farmer"
    && profileType !== "fpo"
  ) {
    return (
      <UnsupportedProfileRole
        role={profileType}
      />
    );
  }

  const nav =
    profileType === "fpo"
      ? FPO_NAV
      : FARMER_NAV;

  const scrollTo = (id) => {
    setActiveSection(id);
    document
      .getElementById(id)
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
  };

  const handleExport = async () => {
    const payload =
      await exportProfile();

    downloadProfileJson(payload);
  };

  return (
    <div className="mt-font-body min-h-screen px-4 py-6 text-slate-900 md:px-6">
      <div className="mx-auto max-w-6xl">
        <div className="space-y-5">
          <ProfileHeader
            user={user}
            profile={profile}
            profileType={profileType}
            completionPercentage={
              completionPercentage
            }
            onboardingStatus={
              onboardingStatus
            }
          />

          <div className="grid gap-5 lg:grid-cols-[250px_1fr]">
            <div className="lg:sticky lg:top-5 lg:self-start">
              <ProfileNavigation
                items={nav}
                activeSection={activeSection}
                onSelect={scrollTo}
              />
              <div
                className="mt-fade-up mt-4 rounded-2xl border border-slate-200 bg-white p-4 text-xs leading-5 text-slate-500 shadow-[0_4px_14px_rgba(15,23,42,0.04)]"
                style={{ "--mt-d": "120ms" }}
              >
                <p className="mt-font-mono mb-1.5 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                  How completion works
                </p>
                Onboarding checks use only the core required fields. The
                completion percentage reflects a wider optional
                profile-fill score.
              </div>
            </div>

            <main className="space-y-5">
              <ProfileMissingFields
                missingFields={
                  missingFields
                }
              />

              {profileType === "fpo" ? (
                <FpoProfileForm
                  user={user}
                  profile={profile}
                  setupRequired={
                    setupRequired
                  }
                  saving={saving}
                  exporting={exporting}
                  savedAt={savedAt}
                  onSave={saveFpoProfile}
                  onExport={handleExport}
                />
              ) : (
                <FarmerProfileForm
                  user={user}
                  profile={profile}
                  saving={saving}
                  exporting={exporting}
                  savedAt={savedAt}
                  onSave={
                    saveFarmerProfile
                  }
                  onExport={handleExport}
                />
              )}
            </main>
          </div>
        </div>
      </div>
    </div>
  );
}
