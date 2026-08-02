import {
  useState,
} from "react";
import {
  BarChart3,
  Check,
  Cloud,
  Database,
  Leaf,
  MapPin,
  Satellite,
  Shield,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import { motion as Motion } from "framer-motion";

import { ProfileGrid, ProfileSection } from "@/features/profile/components/ProfileSection";

const PLANS = [
  {
    id: "maatitrace",
    name: "MaatiTrace",
    audience: "Individual Farmer",
    price: "Free",
    cadence: "5-day satellite cadence",
    storage: "2 GB storage",
    tagline:
      "For individual farmers starting their satellite land intelligence journey.",
    highlights: [
      "Up to 3 parcels",
      "Sentinel-2 monitoring",
      "Basic NDVI and crop health",
      "Verified land certificate",
      "Link to one FPO",
    ],
    icon: Leaf,
  },
  {
    id: "maatitrace_pro",
    name: "MaatiTrace Pro",
    audience: "FPOs and Institutions",
    price: "Rs. 1,999/mo",
    cadence: "Real-time API plus bulk workflows",
    storage: "50 GB storage",
    tagline:
      "For FPOs, cooperatives and institutions managing many farmers at scale.",
    highlights: [
      "Unlimited farms",
      "Premium satellite stack",
      "Advanced NDVI, moisture and yield models",
      "Bulk data pipeline",
      "Block and district dashboards",
    ],
    icon: Sparkles,
  },
];

const CAPABILITIES = [
  {
    label: "Land parcels",
    icon: MapPin,
    maatitrace: "Up to 3",
    pro: "Unlimited",
  },
  {
    label: "Satellite imagery",
    icon: Satellite,
    maatitrace: "Sentinel-2",
    pro: "Sentinel-2 plus SAR",
  },
  {
    label: "Crop health",
    icon: BarChart3,
    maatitrace: "Basic indices",
    pro: "Per-H3 trends",
  },
  {
    label: "Memberships",
    icon: Users,
    maatitrace: "Self",
    pro: "Unlimited",
  },
  {
    label: "Bulk upload",
    icon: Database,
    maatitrace: false,
    pro: true,
  },
  {
    label: "API access",
    icon: Zap,
    maatitrace: false,
    pro: true,
  },
  {
    label: "Verified certificate",
    icon: Shield,
    maatitrace: true,
    pro: true,
  },
];

function CapabilityValue({
  value,
  strong = false,
}) {
  if (value === true) {
    return (
      <Check className="mx-auto h-4 w-4 text-[color:var(--mt-forest)]" />
    );
  }

  if (value === false) {
    return (
      <span className="text-slate-300">
        -
      </span>
    );
  }

  return (
    <span
      className={`text-xs ${
        strong
          ? "font-bold text-emerald-700"
          : "font-medium text-slate-600"
      }`}
    >
      {value}
    </span>
  );
}

function PlanCard({
  plan,
  currentPlan,
  selectedPlan,
  onSelect,
}) {
  const Icon = plan.icon;
  const isCurrent =
    currentPlan === plan.id;
  const isSelected =
    selectedPlan === plan.id;

  return (
    <Motion.button
      type="button"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.45,
        ease: [0.16, 1, 0.3, 1],
      }}
      onClick={() => onSelect(plan.id)}
      className={`relative flex h-full flex-col rounded-[1.5rem] border-2 bg-white p-5 text-left shadow-sm transition-all duration-300 hover:-translate-y-0.5 ${
        isSelected
          ? "border-[color:var(--mt-forest)] shadow-[0_16px_40px_rgba(16,185,129,0.14)]"
          : "border-slate-200 hover:border-emerald-200"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
              isSelected
                ? "bg-[color:var(--mt-forest-deep)]"
                : "bg-[color:var(--mt-forest-soft)]"
            }`}
          >
            <Icon
              className={`h-5 w-5 ${
                isSelected
                  ? "text-white"
                  : "text-[color:var(--mt-forest)]"
              }`}
            />
          </span>
          <div>
            <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              {plan.audience}
            </p>
            <h3 className="mt-font-display mt-1 text-xl font-semibold text-slate-950">
              {plan.name}
            </h3>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          {isCurrent ? (
            <span className="rounded-full bg-[color:var(--mt-forest-soft)] px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-[color:var(--mt-forest-deep)]">
              Current plan
            </span>
          ) : null}
          {isSelected ? (
            <span className="rounded-full bg-emerald-600 px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
              Selected
            </span>
          ) : null}
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-500">
        {plan.tagline}
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-100 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600">
          <Cloud className="h-3.5 w-3.5 text-[color:var(--mt-forest)]" />
          {plan.storage}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-xl border border-slate-100 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600">
          <Zap className="h-3.5 w-3.5 text-[color:var(--mt-harvest)]" />
          {plan.cadence}
        </span>
      </div>

      <p className="mt-5 text-3xl font-black text-slate-950">
        {plan.price}
      </p>

      <ul className="mt-5 space-y-3 border-t border-slate-100 pt-5">
        {plan.highlights.map((feature) => (
          <li
            key={feature}
            className="flex items-start gap-2.5 text-sm text-slate-600"
          >
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[color:var(--mt-forest-soft)]">
              <Check className="h-3 w-3 text-[color:var(--mt-forest)]" />
            </span>
            {feature}
          </li>
        ))}
      </ul>
    </Motion.button>
  );
}

export function ProfilePlansSection() {
  const currentPlan = "maatitrace";
  const [selectedPlan, setSelectedPlan] =
    useState(currentPlan);

  return (
    <ProfileSection
      id="plan"
      title="Your Plan"
      eyebrow="Frontend preview only"
      icon={Sparkles}
    >
      <div className="rounded-[1.25rem] border border-emerald-100 bg-[color:var(--mt-forest-soft)] p-4 text-sm leading-6 text-emerald-900">
        <strong>MaatiTrace</strong> is your current default plan. Plan
        selection here is only local UI state for now; backend billing and
        entitlement persistence will be added later.
      </div>

      <ProfileGrid>
        {PLANS.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            currentPlan={currentPlan}
            selectedPlan={selectedPlan}
            onSelect={setSelectedPlan}
          />
        ))}
      </ProfileGrid>

      <div className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-[0_4px_14px_rgba(15,23,42,0.04)]">
        <div className="flex items-center gap-2 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-5 py-4">
          <BarChart3 className="h-4 w-4 text-[color:var(--mt-forest)]" />
          <h3 className="text-sm font-bold text-slate-800">
            Feature comparison
          </h3>
          <span className="mt-font-mono ml-auto text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
            UI preview
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50/60">
                <th className="px-5 py-4 text-left text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Capability
                </th>
                <th className="px-5 py-4 text-center text-xs font-black text-slate-800">
                  MaatiTrace
                </th>
                <th className="bg-emerald-50/50 px-5 py-4 text-center text-xs font-black text-emerald-700">
                  MaatiTrace Pro
                </th>
              </tr>
            </thead>
            <tbody>
              {CAPABILITIES.map((row, index) => {
                const Icon = row.icon;

                return (
                  <tr
                    key={row.label}
                    className={`border-t border-slate-100 ${
                      index % 2
                        ? "bg-slate-50/30"
                        : ""
                    }`}
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[color:var(--mt-forest-soft)]">
                          <Icon className="h-3.5 w-3.5 text-[color:var(--mt-forest)]" />
                        </span>
                        <span className="text-xs font-semibold text-slate-700">
                          {row.label}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <CapabilityValue value={row.maatitrace} />
                    </td>
                    <td className="bg-emerald-50/30 px-5 py-3.5 text-center">
                      <CapabilityValue
                        value={row.pro}
                        strong
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </ProfileSection>
  );
}
