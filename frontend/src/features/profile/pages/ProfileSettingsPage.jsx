import {
  useEffect,
  useState,
} from "react";
import { motion as Motion } from "framer-motion";
import {
  Building2,
  Check,
  ChevronLeft,
  Download,
  FileText,
  MapPin,
  ShieldCheck,
  Shield,
  User,
  Wheat,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

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
  getFpoVerificationStatus,
  submitFpoVerification,
} from "@/lib/api/fpo";
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
  { id: "export", label: "Export", icon: Download },
];

const FPO_NAV = [
  { id: "organisation", label: "Organisation", icon: Building2 },
  { id: "contact", label: "Contact", icon: User },
  { id: "location", label: "Location", icon: MapPin },
  { id: "operations", label: "Operations", icon: Wheat },
  { id: "verification", label: "Verification", icon: Shield },
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
  const navigate = useNavigate();
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
  const [verification, setVerification] = useState(null);
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [verificationError, setVerificationError] = useState("");

  useEffect(() => {
    if (profileType === "fpo") {
      setActiveSection("organisation");
    } else {
      setActiveSection("account");
    }
  }, [profileType]);

  useEffect(() => {
    if (profileType !== "fpo") return undefined;
    let active = true;
    getFpoVerificationStatus()
      .then((payload) => { if (active) setVerification(payload); })
      .catch(() => { if (active) setVerification(null); });
    return () => { active = false; };
  }, [profileType, profile]);

  const handleSubmitVerification = async () => {
    setVerificationLoading(true);
    setVerificationError("");
    try {
      const payload = await submitFpoVerification();
      setVerification(payload);
    } catch (requestError) {
      setVerificationError(requestError?.message || "Complete the required profile fields before submitting.");
    } finally {
      setVerificationLoading(false);
    }
  };

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
          <button
            type="button"
            onClick={() => navigate("/farmer/me")}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 text-sm font-semibold text-slate-600 shadow-sm transition-colors hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-800 md:hidden"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back to dashboard
          </button>
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
                <>
                  <FpoProfileForm
                    user={user}
                    profile={profile}
                    setupRequired={setupRequired}
                    saving={saving}
                    exporting={exporting}
                    savedAt={savedAt}
                    onSave={saveFpoProfile}
                    onExport={handleExport}
                  />
                  <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Verification</p>
                      <h2 className="mt-1 text-lg font-black text-slate-900">Submit your FPO for review</h2>
                      <p className="mt-1 text-sm leading-6 text-slate-500">Once required profile details are complete, submit them to MaatiTrace administrators for approval.</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-slate-600">{String(verification?.verification_status || "PROFILE_INCOMPLETE").replaceAll("_", " ")}</span>
                  </div>
                  {verificationError ? <p className="mt-3 text-sm text-rose-600">{verificationError}</p> : null}
                  <button type="button" onClick={handleSubmitVerification} disabled={verificationLoading || !profile || Boolean(verification?.verification_status && ["SUBMITTED", "UNDER_REVIEW", "APPROVED"].includes(verification.verification_status))} className="mt-4 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50">
                    {verificationLoading ? "Submitting…" : "Submit for verification"}
                  </button>
                  </section>
                </>
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
