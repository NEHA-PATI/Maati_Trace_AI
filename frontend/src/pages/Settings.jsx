import React, { useEffect, useMemo, useState } from "react";
import {
  Building2,
  Check,
  Download,
  Edit3,
  FileText,
  Lock,
  MapPin,
  Shield,
  User,
  Wheat,
} from "lucide-react";
import { motion } from "framer-motion";
import { getStoredUser } from "@/lib/auth/session";
import { getMyFarmerProfile, updateMyFarmerProfile, exportMyFarmerProfile } from "@/lib/api/farmer";
import { getMyFpo, updateMyFpoProfile, exportMyFpoProfile } from "@/lib/api/fpo";

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
  { id: "export", label: "Export", icon: Download },
];

export default function Settings() {
  const user = getStoredUser();
  const [profile, setProfile] = useState({});
  const [saved, setSaved] = useState(false);
  const [activeSection, setActiveSection] = useState(user?.role === "fpo" ? "organisation" : "account");

  useEffect(() => {
    let mounted = true;
    const loader = user?.role === "fpo" ? getMyFpo() : getMyFarmerProfile();
    loader
      .then((payload) => mounted && setProfile(payload || {}))
      .catch(() => mounted && setProfile({}));
    return () => {
      mounted = false;
    };
  }, [user?.role]);

  const nav = user?.role === "fpo" ? FPO_NAV : FARMER_NAV;
  const completion = useMemo(() => calculateProfileCompletion(user?.role, profile), [user?.role, profile]);

  const save = async () => {
    if (user?.role === "fpo") {
      await updateMyFpoProfile(profile);
    } else {
      await updateMyFarmerProfile(profile);
    }
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2200);
  };

  const exportProfile = async () => {
    const payload = user?.role === "fpo" ? await exportMyFpoProfile() : await exportMyFarmerProfile();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `maatitrace-${user?.role || "profile"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const scrollTo = (id) => {
    setActiveSection(id);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f6f8f4_0%,#eef2ec_100%)] px-4 py-6 text-slate-900 md:px-6">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)]"
        >
          <div className="relative h-24 bg-[linear-gradient(135deg,#0f5132_0%,#1f6f4a_45%,#365a2e_100%)]">
            <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(rgba(255,255,255,0.8)_1px,transparent_1px)] [background-size:20px_20px]" />
          </div>
          <div className="px-6 pb-6">
            <div className="-mt-10 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
              <div className="flex items-end gap-4">
                <div className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-white bg-slate-100 shadow-lg">
                  <User className="h-10 w-10 text-slate-300" />
                </div>
                <div className="pb-1">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-500">Profile settings</p>
                  <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-950">
                    {user?.full_name || "Your profile"}
                  </h1>
                  <p className="mt-1 text-sm text-slate-600">{user?.email}</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <StatCard label="Completion" value={`${completion}%`} />
                <StatCard label="Verification" value="Pending" subdued />
                <button
                  onClick={exportProfile}
                  className="inline-flex h-11 items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                >
                  <Download className="h-4 w-4" />
                  Export JSON
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {saved && (
          <div className="fixed left-1/2 top-6 z-50 -translate-x-1/2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800 shadow-lg">
            Changes saved
          </div>
        )}

        <div className="mt-6 grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="lg:sticky lg:top-6 lg:h-fit">
            <div className="rounded-[1.5rem] border border-slate-200 bg-white p-3 shadow-sm">
              {nav.map((item) => {
                const Icon = item.icon;
                const active = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => scrollTo(item.id)}
                    className={`mb-1 flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm font-semibold transition-colors ${
                      active ? "bg-emerald-50 text-emerald-800" : "text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </button>
                );
              })}
              <div className="mt-2 border-t border-slate-200 pt-3">
                <div className="rounded-2xl bg-slate-50 px-3 py-3 text-xs leading-5 text-slate-600">
                  MaatiTrace stores verification status and masked identifiers where possible.
                </div>
              </div>
            </div>
          </aside>

          <main className="space-y-5">
            {user?.role === "fpo" ? (
              <>
                <SettingsSection id="organisation" icon={Building2} title="Organisation" subtitle="Core organisational identity and registration details">
                  <Grid>
                    <Field label="FPO Name" value={profile.fpo_name || ""} onChange={(v) => setProfile((p) => ({ ...p, fpo_name: v }))} />
                    <Field label="Registration Number" value={profile.registration_number || ""} onChange={(v) => setProfile((p) => ({ ...p, registration_number: v }))} />
                    <Field label="Registration Type" value={profile.registration_type || ""} onChange={(v) => setProfile((p) => ({ ...p, registration_type: v }))} />
                    <Field label="Date of Registration" type="date" value={profile.date_of_registration || ""} onChange={(v) => setProfile((p) => ({ ...p, date_of_registration: v }))} />
                    <Field label="Promoted By" value={profile.promoted_by || ""} onChange={(v) => setProfile((p) => ({ ...p, promoted_by: v }))} />
                    <Field label="Promoting Institution" value={profile.promoting_institution_name || ""} onChange={(v) => setProfile((p) => ({ ...p, promoting_institution_name: v }))} />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="contact" icon={User} title="Contact" subtitle="Primary contact person and communication channels">
                  <Grid>
                    <Field label="Contact Person" value={profile.contact_person_name || ""} onChange={(v) => setProfile((p) => ({ ...p, contact_person_name: v }))} />
                    <Field label="Designation" value={profile.contact_person_designation || ""} onChange={(v) => setProfile((p) => ({ ...p, contact_person_designation: v }))} />
                    <Field label="Phone" value={profile.contact_phone || ""} onChange={(v) => setProfile((p) => ({ ...p, contact_phone: v }))} />
                    <Field label="Alternate Phone" value={profile.alternate_phone || ""} onChange={(v) => setProfile((p) => ({ ...p, alternate_phone: v }))} />
                    <Field label="Email" type="email" value={profile.contact_email || ""} onChange={(v) => setProfile((p) => ({ ...p, contact_email: v }))} />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="location" icon={MapPin} title="Location" subtitle="Regional footprint and office location">
                  <Grid>
                    <Field label="State" value={profile.state_name || "Odisha"} onChange={(v) => setProfile((p) => ({ ...p, state_name: v }))} />
                    <Field label="District" value={profile.district_name || ""} onChange={(v) => setProfile((p) => ({ ...p, district_name: v }))} />
                    <Field label="Block" value={profile.block_name || ""} onChange={(v) => setProfile((p) => ({ ...p, block_name: v }))} />
                    <Field label="Village" value={profile.village_name || ""} onChange={(v) => setProfile((p) => ({ ...p, village_name: v }))} />
                    <Field label="Pincode" value={profile.pincode || ""} onChange={(v) => setProfile((p) => ({ ...p, pincode: v }))} />
                    <Field label="Office Address" value={profile.office_address || ""} onChange={(v) => setProfile((p) => ({ ...p, office_address: v }))} multiline />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="operations" icon={Wheat} title="Operations" subtitle="Crop focus and service coverage">
                  <Grid>
                    <Field label="Main Commodities" value={Array.isArray(profile.main_commodities) ? profile.main_commodities.join(", ") : profile.main_commodities || ""} onChange={(v) => setProfile((p) => ({ ...p, main_commodities: v }))} />
                    <Field label="Member Count" type="number" value={profile.member_count || ""} onChange={(v) => setProfile((p) => ({ ...p, member_count: v }))} />
                    <Field label="Active Members" type="number" value={profile.active_member_count || ""} onChange={(v) => setProfile((p) => ({ ...p, active_member_count: v }))} />
                    <Field label="Services Provided" value={Array.isArray(profile.services_provided) ? profile.services_provided.join(", ") : profile.services_provided || ""} onChange={(v) => setProfile((p) => ({ ...p, services_provided: v }))} />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="verification" icon={Shield} title="Verification" subtitle="Status and document readiness">
                  <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                    Verification status remains pending until the organisation documents are reviewed.
                  </div>
                </SettingsSection>
              </>
            ) : (
              <>
                <SettingsSection id="account" icon={User} title="Account" subtitle="Core identity and contact information">
                  <Grid>
                    <Field label="Full Name" value={profile.full_name || ""} onChange={(v) => setProfile((p) => ({ ...p, full_name: v }))} />
                    <Field label="Phone Number" value={profile.phone_number || ""} onChange={(v) => setProfile((p) => ({ ...p, phone_number: v }))} />
                    <Field label="Email" type="email" value={profile.email || ""} onChange={(v) => setProfile((p) => ({ ...p, email: v }))} />
                    <Field label="Preferred Language" value={profile.preferred_language || ""} onChange={(v) => setProfile((p) => ({ ...p, preferred_language: v }))} />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="identity" icon={Shield} title="Identity" subtitle="KYC and masked identifiers">
                  <Grid>
                    <Field label="Gender" value={profile.gender || ""} onChange={(v) => setProfile((p) => ({ ...p, gender: v }))} />
                    <Field label="Date of Birth" type="date" value={profile.date_of_birth || ""} onChange={(v) => setProfile((p) => ({ ...p, date_of_birth: v }))} />
                    <Field label="Aadhaar Last 4" value={profile.aadhaar_last4 || ""} onChange={(v) => setProfile((p) => ({ ...p, aadhaar_last4: v.replace(/\D/g, "").slice(0, 4) }))} />
                    <ReadOnlyField label="KYC Status" value={profile.kyc_status || "pending"} />
                  </Grid>
                  <div className="mt-4 rounded-[1.25rem] border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                    MaatiTrace stores verification status and masked identifiers where possible. Full Aadhaar is not shown here.
                  </div>
                </SettingsSection>

                <SettingsSection id="location" icon={MapPin} title="Location" subtitle="Place and administrative geography">
                  <Grid>
                    <Field label="State" value={profile.state_name || "Odisha"} onChange={(v) => setProfile((p) => ({ ...p, state_name: v }))} />
                    <Field label="District" value={profile.district_name || ""} onChange={(v) => setProfile((p) => ({ ...p, district_name: v }))} />
                    <Field label="Block" value={profile.block_name || ""} onChange={(v) => setProfile((p) => ({ ...p, block_name: v }))} />
                    <Field label="Village" value={profile.village_name || ""} onChange={(v) => setProfile((p) => ({ ...p, village_name: v }))} />
                    <Field label="Gram Panchayat" value={profile.gram_panchayat || ""} onChange={(v) => setProfile((p) => ({ ...p, gram_panchayat: v }))} />
                    <Field label="Pincode" value={profile.pincode || ""} onChange={(v) => setProfile((p) => ({ ...p, pincode: v }))} />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="role" icon={Wheat} title="Farming Profile" subtitle="Land and crop details">
                  <Grid>
                    <Field label="FPO ID" value={profile.fpo_id || ""} onChange={(v) => setProfile((p) => ({ ...p, fpo_id: v }))} />
                    <Field label="Farmer Type" value={profile.farmer_type || ""} onChange={(v) => setProfile((p) => ({ ...p, farmer_type: v }))} />
                    <Field label="Total Landholding (acres)" type="number" value={profile.total_landholding_acres || ""} onChange={(v) => setProfile((p) => ({ ...p, total_landholding_acres: v }))} />
                    <Field label="Cultivated Area (acres)" type="number" value={profile.cultivated_area_acres || ""} onChange={(v) => setProfile((p) => ({ ...p, cultivated_area_acres: v }))} />
                    <Field label="Primary Crop" value={profile.primary_crop || ""} onChange={(v) => setProfile((p) => ({ ...p, primary_crop: v }))} />
                    <Field label="Irrigation Status" value={profile.irrigation_status || ""} onChange={(v) => setProfile((p) => ({ ...p, irrigation_status: v }))} />
                  </Grid>
                </SettingsSection>

                <SettingsSection id="consent" icon={Check} title="Consent" subtitle="Shared data permissions">
                  <ConsentRow label="Location use" checked={!!profile.consent_location_use} onToggle={(v) => setProfile((p) => ({ ...p, consent_location_use: v }))} />
                  <ConsentRow label="Data processing" checked={!!profile.consent_data_processing} onToggle={(v) => setProfile((p) => ({ ...p, consent_data_processing: v }))} />
                  <ConsentRow label="Advisory messages" checked={!!profile.consent_advisory_messages} onToggle={(v) => setProfile((p) => ({ ...p, consent_advisory_messages: v }))} />
                  <ConsentRow label="FPO data sharing" checked={!!profile.consent_fpo_data_sharing} onToggle={(v) => setProfile((p) => ({ ...p, consent_fpo_data_sharing: v }))} />
                </SettingsSection>
              </>
            )}

            <div id="export" className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Export</p>
                  <h2 className="mt-1 text-xl font-black text-slate-950">Download your profile</h2>
                  <p className="mt-2 text-sm text-slate-600">Export JSON for records or backup. PDF can be added later if needed.</p>
                </div>
                <FileText className="h-9 w-9 text-emerald-700" />
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={save}
                  className="inline-flex h-11 items-center gap-2 rounded-2xl bg-slate-950 px-5 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
                >
                  <Edit3 className="h-4 w-4" />
                  Save changes
                </button>
                <button
                  type="button"
                  onClick={exportProfile}
                  className="inline-flex h-11 items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
                >
                  <Download className="h-4 w-4" />
                  Export JSON
                </button>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

function SettingsSection({ id, icon: Icon, title, subtitle, children }) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm"
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950">
            <Icon className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-base font-black text-slate-950">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
          </div>
        </div>
      </div>
      <div className="p-5">{children}</div>
    </motion.section>
  );
}

function Grid({ children }) {
  return <div className="grid gap-4 md:grid-cols-2">{children}</div>;
}

function Field({ label, value, onChange, multiline, type = "text" }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">{label}</span>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="min-h-28 w-full rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm text-slate-900 outline-none transition-colors focus:border-emerald-700"
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm text-slate-900 outline-none transition-colors focus:border-emerald-700"
        />
      )}
    </label>
  );
}

function ReadOnlyField({ label, value }) {
  return (
    <div>
      <span className="mb-1.5 block text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">{label}</span>
      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm font-semibold text-slate-700">{value}</div>
    </div>
  );
}

function ConsentRow({ label, checked, onToggle }) {
  return (
    <button
      type="button"
      onClick={() => onToggle(!checked)}
      className={`mb-3 flex w-full items-center justify-between rounded-2xl border px-4 py-4 text-left transition-colors ${
        checked ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-slate-50 hover:bg-slate-100"
      }`}
    >
      <span className="text-sm font-semibold text-slate-800">{label}</span>
      <span className={`flex h-5 w-5 items-center justify-center rounded-md border ${checked ? "border-emerald-700 bg-emerald-700" : "border-slate-300 bg-white"}`}>
        {checked ? <Check className="h-3.5 w-3.5 text-white" /> : null}
      </span>
    </button>
  );
}

function StatCard({ label, value, subdued }) {
  return (
    <div className={`rounded-2xl border px-4 py-3 ${subdued ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-black text-slate-950">{value}</p>
    </div>
  );
}

function calculateProfileCompletion(role, profile) {
  const sections =
    role === "fpo"
      ? [
          ["fpo_name", "registration_number", "registration_type", "date_of_registration"],
          ["contact_person_name", "contact_person_designation", "contact_phone", "contact_email"],
          ["state_name", "district_name", "block_name", "office_address"],
          ["main_commodities", "member_count", "active_member_count", "services_provided"],
          ["verification_status"],
        ]
      : [
          ["full_name", "phone_number", "email", "preferred_language"],
          ["gender", "date_of_birth", "aadhaar_last4", "kyc_status"],
          ["state_name", "district_name", "block_name", "village_name"],
          ["fpo_id", "farmer_type", "total_landholding_acres", "primary_crop", "irrigation_status"],
          ["consent_location_use", "consent_data_processing", "consent_advisory_messages", "consent_fpo_data_sharing"],
        ];

  let filled = 0;
  let total = 0;
  sections.forEach((group) => {
    group.forEach((field) => {
      total += 1;
      const value = profile?.[field];
      if (Array.isArray(value)) {
        if (value.length) filled += 1;
      } else if (value !== undefined && value !== null && `${value}`.trim() !== "") {
        filled += 1;
      }
    });
  });

  return total ? Math.round((filled / total) * 100) : 0;
}
