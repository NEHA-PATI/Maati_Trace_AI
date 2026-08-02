import {
  useState,
} from "react";
import { Link } from "react-router-dom";
import {
  motion as Motion,
  AnimatePresence,
} from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Building2,
  Check,
  ChevronDown,
  Cloud,
  Database,
  Globe,
  Layers,
  Leaf,
  MapPin,
  Minus,
  Quote,
  Satellite,
  Shield,
  Sparkles,
  Star,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import PublicNav from "@/components/layout/PublicNav";
import { useAuth } from "@/features/auth/context/useAuth";

const TRUST_STATS = [
  {
    value: "140K+",
    label: "Farmers Registered",
    icon: Users,
    color: "text-blue-500 bg-blue-50",
  },
  {
    value: "2.4M ha",
    label: "Land Tracked",
    icon: Globe,
    color: "text-emerald-500 bg-emerald-50",
  },
  {
    value: "99.2%",
    label: "Verification Accuracy",
    icon: Shield,
    color: "text-amber-500 bg-amber-50",
  },
  {
    value: "5-day",
    label: "Satellite Revisit",
    icon: Satellite,
    color: "text-violet-500 bg-violet-50",
  },
];

const PLANS = [
  {
    id: "maatitrace",
    name: "MaatiTrace",
    tagline:
      "For individual farmers starting their satellite land intelligence journey.",
    storage: {
      icon: Cloud,
      value: "2 GB storage",
    },
    monthly: 0,
    annual: 0,
    cta: "Start Free",
    ctaTo: "/register",
    audience: "Individual Farmer",
    highlights: [
      {
        icon: TrendingUp,
        label: "Up to 3 parcels",
      },
      {
        icon: Zap,
        label: "5-day satellite cadence",
      },
    ],
    features: [
      {
        icon: MapPin,
        title: "Register up to 3 land parcels",
        desc: "GPS-tagged farm boundaries with H3 grid overlay.",
      },
      {
        icon: Satellite,
        title: "Sentinel-2 satellite monitoring",
        desc: "10 m multispectral imagery every 5 to 10 days.",
      },
      {
        icon: BarChart3,
        title: "Basic NDVI and crop health",
        desc: "Vegetation index per parcel, updated each scene.",
      },
      {
        icon: Shield,
        title: "Verified land certificate",
        desc: "Tamper-proof farm health report for credit and insurance.",
      },
      {
        icon: Users,
        title: "Link to one FPO",
        desc: "Optional connection with your farmer producer organisation.",
      },
    ],
  },
  {
    id: "maatitrace_pro",
    name: "MaatiTrace Pro",
    tagline:
      "For FPOs, cooperatives and institutions managing many farmers at scale.",
    storage: {
      icon: Cloud,
      value: "50 GB storage",
    },
    monthly: 1999,
    annual: 19999,
    cta: "Get MaatiTrace Pro",
    ctaTo: "/register",
    recommended: true,
    audience: "FPOs and Institutions",
    highlights: [
      {
        icon: TrendingUp,
        label: "Unlimited farms",
      },
      {
        icon: Zap,
        label: "Real-time API plus bulk",
      },
    ],
    features: [
      {
        icon: MapPin,
        title: "Unlimited land parcels",
        desc: "Register every member farm with bulk CSV upload.",
      },
      {
        icon: Satellite,
        title: "Premium satellite stack",
        desc: "Sentinel-2 plus Sentinel-1 SAR and Landsat, cloud-masked.",
      },
      {
        icon: BarChart3,
        title: "Advanced NDVI, moisture and yield models",
        desc: "Per-H3 cell analytics with seasonal trend lines.",
      },
      {
        icon: Users,
        title: "Unlimited farmer memberships",
        desc: "Invite, manage and audit your entire FPO portfolio.",
      },
      {
        icon: Database,
        title: "Bulk data pipeline",
        desc: "Batch raster processing with full audit logs.",
      },
      {
        icon: Layers,
        title: "Block and district dashboards",
        desc: "Aggregated intelligence for officers and admins.",
      },
      {
        icon: Shield,
        title: "Priority verification and API access",
        desc: "Faster KYC turnaround plus REST API access.",
      },
    ],
  },
];

const COMPARE_ROWS = [
  {
    feature: "Land parcels",
    icon: MapPin,
    basic: "Up to 3",
    pro: "Unlimited",
  },
  {
    feature: "Satellite imagery",
    icon: Satellite,
    basic: "Sentinel-2",
    pro: "Sentinel-2 plus SAR and Landsat",
  },
  {
    feature: "NDVI and crop health",
    icon: BarChart3,
    basic: "Basic indices",
    pro: "Per-H3 plus trend models",
  },
  {
    feature: "Soil moisture SAR",
    icon: Satellite,
    basic: false,
    pro: true,
  },
  {
    feature: "Farmer memberships",
    icon: Users,
    basic: "1 self",
    pro: "Unlimited",
  },
  {
    feature: "Bulk CSV upload",
    icon: Database,
    basic: false,
    pro: true,
  },
  {
    feature: "Block and district dashboards",
    icon: Layers,
    basic: false,
    pro: true,
  },
  {
    feature: "REST API access",
    icon: Zap,
    basic: false,
    pro: true,
  },
  {
    feature: "Verified land certificates",
    icon: Shield,
    basic: true,
    pro: true,
  },
  {
    feature: "Priority KYC and support",
    icon: Star,
    basic: false,
    pro: true,
  },
];

const TESTIMONIALS = [
  {
    quote:
      "MaatiTrace Pro put every member farm on a single map. Our loan approval cycle dropped from 6 weeks to 11 days.",
    author: "Lakshmi Narayana",
    role: "CEO, Puri District FPO",
    accent: "bg-emerald-500",
  },
  {
    quote:
      "I registered 3 acres for free and got a satellite-backed land certificate my bank actually accepted.",
    author: "Ramesh Sahoo",
    role: "Smallholder Farmer, Odisha",
    accent: "bg-blue-500",
  },
];

const FAQS = [
  {
    q: "Is MaatiTrace really free for individual farmers?",
    a: "Yes. The free tier supports up to 3 land parcels with Sentinel-2 monitoring and verified certificates.",
  },
  {
    q: "How are Pro plans billed?",
    a: "Monthly billing is Rs. 1,999 per month. Annual billing is Rs. 19,999 per year. GST will be handled when backend billing is added.",
  },
  {
    q: "Can I upgrade or downgrade later?",
    a: "Yes. The UI is ready for plan selection, and backend billing plus entitlement persistence will be connected later.",
  },
  {
    q: "Is my Aadhaar data stored?",
    a: "No. MaatiTrace stores only the last 4 digits and verification status. Full Aadhaar is not persisted.",
  },
  {
    q: "Do you support FPOs with many farmers?",
    a: "Yes. Pro is designed for bulk upload, unlimited memberships and block-level aggregate dashboards.",
  },
];

function normalizePlanId(plan) {
  if (plan === "pro" || plan === "maatitrace_pro") {
    return "maatitrace_pro";
  }

  return "maatitrace";
}

function BillingToggle({
  billing,
  setBilling,
}) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="inline-flex rounded-full border border-emerald-100 bg-emerald-50 p-1">
        {["monthly", "annual"].map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setBilling(option)}
            className={`rounded-full px-6 py-2 text-xs font-bold capitalize transition-all ${
              billing === option
                ? "bg-emerald-600 text-white shadow-sm"
                : "text-emerald-700 hover:text-emerald-800"
            }`}
          >
            {option}
          </button>
        ))}
      </div>
      <p className="flex items-center gap-1.5 text-xs font-bold text-emerald-700">
        <Sparkles
          className="h-3.5 w-3.5"
          strokeWidth={2.5}
        />
        Save 16% when you pay annually
      </p>
    </div>
  );
}

function PlanCard({
  plan,
  billing,
  authenticated,
  currentPlan,
  selectedPlan,
  onSelect,
}) {
  const price =
    billing === "annual"
      ? plan.annual
      : plan.monthly;
  const StorageIcon = plan.storage.icon;
  const isFree = price === 0;
  const isCurrent =
    authenticated && currentPlan === plan.id;
  const isSelected =
    selectedPlan === plan.id;

  return (
    <Motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{
        once: true,
        margin: "-80px",
      }}
      transition={{
        duration: 0.55,
        ease: [0.22, 1, 0.36, 1],
      }}
      className={`relative flex flex-col rounded-2xl border bg-white shadow-sm transition-all ${
        plan.recommended
          ? "border-emerald-500 shadow-xl shadow-emerald-500/10"
          : "border-gray-200"
      } ${
        isSelected
          ? "ring-4 ring-emerald-500/10"
          : ""
      }`}
    >
      {plan.recommended ? (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-emerald-500 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-white shadow-md">
          Recommended
        </div>
      ) : null}

      {isCurrent ? (
        <div className="absolute right-4 top-4 rounded-full bg-emerald-50 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-700">
          Current plan
        </div>
      ) : null}

      <div className="flex flex-1 flex-col p-7">
        <div
          className={`mb-3 inline-flex w-fit items-center gap-1.5 rounded-full px-3 py-1 text-[9px] font-bold uppercase tracking-widest ${
            plan.recommended
              ? "bg-emerald-100 text-emerald-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          <Building2
            className="h-3 w-3"
            strokeWidth={2.5}
          />
          {plan.audience}
        </div>

        <div className="mb-2 flex items-center gap-2">
          <div
            className={`flex h-7 w-7 items-center justify-center rounded-xl ${
              plan.recommended
                ? "bg-emerald-500"
                : "bg-emerald-50"
            }`}
          >
            <Leaf
              className={`h-4 w-4 ${
                plan.recommended
                  ? "text-white"
                  : "text-emerald-500"
              }`}
              strokeWidth={2.5}
            />
          </div>
          <h3 className="text-base font-black text-gray-900">
            {plan.name}
          </h3>
        </div>

        <p className="mb-4 min-h-[34px] text-xs leading-relaxed text-gray-500">
          {plan.tagline}
        </p>

        <div className="mb-4 flex flex-wrap gap-2">
          {plan.highlights.map((highlight) => {
            const HighlightIcon =
              highlight.icon;

            return (
              <span
                key={highlight.label}
                className="inline-flex items-center gap-1 rounded-lg border border-gray-100 bg-gray-50 px-2.5 py-1 text-[10px] font-semibold text-gray-600"
              >
                <HighlightIcon
                  className="h-3 w-3 text-emerald-500"
                  strokeWidth={2.5}
                />
                {highlight.label}
              </span>
            );
          })}
        </div>

        <div className="mb-5 inline-flex w-fit items-center gap-1.5 rounded-xl border border-gray-100 bg-gray-50 px-3 py-1.5">
          <StorageIcon
            className="h-3.5 w-3.5 text-emerald-500"
            strokeWidth={2}
          />
          <span className="text-[11px] font-semibold text-gray-600">
            {plan.storage.value}
          </span>
        </div>

        <div className="mb-1">
          <span className="text-3xl font-black text-gray-900">
            {isFree
              ? "Free"
              : `Rs. ${price.toLocaleString("en-IN")}`}
          </span>
          {!isFree ? (
            <span className="text-sm font-medium text-gray-400">
              /{billing === "annual" ? "yr" : "mo"}
            </span>
          ) : null}
        </div>

        {!isFree && billing === "annual" ? (
          <p className="mb-1 text-xs text-gray-400">
            <span className="line-through">
              Rs. {(plan.monthly * 12).toLocaleString("en-IN")}
            </span>{" "}
            billed yearly
          </p>
        ) : null}
        {!isFree && billing === "monthly" ? (
          <p className="mb-1 text-xs text-gray-400">
            billed monthly, cancel anytime
          </p>
        ) : null}
        {isFree ? (
          <p className="mb-1 text-xs text-gray-400">
            forever free for smallholders
          </p>
        ) : null}

        {authenticated ? (
          <button
            type="button"
            onClick={() => onSelect(plan.id)}
            className={`mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-xl text-sm font-bold transition-all hover:-translate-y-0.5 ${
              isSelected
                ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
            }`}
          >
            {isSelected
              ? "Selected"
              : "Preview Selection"}
            <ArrowRight className="h-4 w-4" />
          </button>
        ) : (
          <Link
            to={plan.ctaTo}
            className={`mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-xl text-sm font-bold transition-all hover:-translate-y-0.5 ${
              plan.recommended
                ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 hover:bg-emerald-600"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
            }`}
          >
            {plan.cta}
            <ArrowRight className="h-4 w-4" />
          </Link>
        )}

        <div className="mt-6 space-y-4 border-t border-gray-100 pt-6">
          {plan.features.map((feature) => {
            const Icon = feature.icon;

            return (
              <div
                key={feature.title}
                className="flex items-start gap-3"
              >
                <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-lg bg-emerald-50">
                  <Icon
                    className="h-3 w-3 text-emerald-500"
                    strokeWidth={2.5}
                  />
                </div>
                <div>
                  <p className="text-xs font-bold leading-snug text-gray-800">
                    {feature.title}
                  </p>
                  <p className="mt-0.5 text-[11px] leading-relaxed text-gray-400">
                    {feature.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Motion.div>
  );
}

function ComparisonValue({
  value,
  strong = false,
}) {
  if (value === true) {
    return (
      <Check
        className="inline-block h-4 w-4 text-emerald-500"
        strokeWidth={3}
      />
    );
  }

  if (value === false) {
    return (
      <Minus
        className="inline-block h-4 w-4 text-gray-300"
        strokeWidth={2.5}
      />
    );
  }

  return (
    <span
      className={`text-[11px] ${
        strong
          ? "font-bold text-emerald-700"
          : "font-medium text-gray-600"
      }`}
    >
      {value}
    </span>
  );
}

function ComparisonTable() {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{
        once: true,
        margin: "-100px",
      }}
      transition={{ duration: 0.55 }}
      className="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm"
    >
      <div className="flex items-center gap-2 border-b border-gray-100 px-6 py-4">
        <Layers
          className="h-4 w-4 text-emerald-500"
          strokeWidth={2.5}
        />
        <h3 className="text-sm font-bold text-gray-800">
          Feature Comparison
        </h3>
        <span className="ml-auto text-[10px] font-medium uppercase tracking-wider text-gray-400">
          side by side
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50/60">
              <th className="px-6 py-4 text-left text-[11px] font-bold uppercase tracking-wider text-gray-400">
                Capability
              </th>
              <th className="px-6 py-4 text-center">
                <span className="text-xs font-black text-gray-800">
                  MaatiTrace
                </span>
                <span className="mt-0.5 block text-[9px] font-semibold uppercase tracking-wider text-gray-400">
                  Free
                </span>
              </th>
              <th className="bg-emerald-50/50 px-6 py-4 text-center">
                <span className="text-xs font-black text-emerald-700">
                  MaatiTrace Pro
                </span>
                <span className="mt-0.5 block text-[9px] font-semibold uppercase tracking-wider text-emerald-600">
                  Rs. 1,999/mo
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {COMPARE_ROWS.map((row, index) => {
              const Icon = row.icon;

              return (
                <tr
                  key={row.feature}
                  className={`border-t border-gray-100 ${
                    index % 2
                      ? "bg-gray-50/30"
                      : ""
                  }`}
                >
                  <td className="px-6 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-emerald-50">
                        <Icon
                          className="h-3 w-3 text-emerald-500"
                          strokeWidth={2.5}
                        />
                      </div>
                      <span className="text-xs font-semibold text-gray-700">
                        {row.feature}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-3.5 text-center">
                    <ComparisonValue value={row.basic} />
                  </td>
                  <td className="bg-emerald-50/30 px-6 py-3.5 text-center">
                    <ComparisonValue
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
    </Motion.div>
  );
}

function TestimonialCard({
  testimonial,
  index,
}) {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{
        once: true,
        margin: "-80px",
      }}
      transition={{
        duration: 0.5,
        delay: index * 0.1,
      }}
      className="flex flex-col gap-4 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm"
    >
      <Quote
        className="h-6 w-6 text-emerald-400"
        strokeWidth={2.5}
      />
      <p className="flex-1 text-sm leading-relaxed text-gray-700">
        {testimonial.quote}
      </p>
      <div className="flex items-center gap-3 border-t border-gray-100 pt-3">
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-full ${testimonial.accent}`}
        >
          <span className="text-xs font-black text-white">
            {testimonial.author.charAt(0)}
          </span>
        </div>
        <div>
          <p className="text-xs font-bold text-gray-800">
            {testimonial.author}
          </p>
          <p className="text-[10px] text-gray-400">
            {testimonial.role}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-0.5">
          {[...Array(5)].map((_, index) => (
            <Star
              key={index}
              className="h-3 w-3 text-amber-400"
              fill="currentColor"
            />
          ))}
        </div>
      </div>
    </Motion.div>
  );
}

function FaqItem({
  item,
  index,
}) {
  const [open, setOpen] =
    useState(index === 0);

  return (
    <div className="border-b border-gray-100 last:border-b-0">
      <button
        type="button"
        onClick={() =>
          setOpen((value) => !value)
        }
        className="flex w-full items-center justify-between gap-4 py-4 text-left"
      >
        <span className="text-sm font-bold text-gray-800">
          {item.q}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-gray-400 transition-transform ${
            open ? "rotate-180" : ""
          }`}
          strokeWidth={2.5}
        />
      </button>
      <AnimatePresence>
        {open ? (
          <Motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{
              height: "auto",
              opacity: 1,
            }}
            exit={{
              height: 0,
              opacity: 0,
            }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <p className="pb-4 pr-8 text-xs leading-relaxed text-gray-500">
              {item.a}
            </p>
          </Motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

function PlansContent({
  authenticated,
  user,
}) {
  const [billing, setBilling] =
    useState("annual");
  const currentPlan =
    normalizePlanId(user?.plan);
  const [selectedPlan, setSelectedPlan] =
    useState(currentPlan);

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-emerald-50/40 via-white to-white font-['Poppins',sans-serif]">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(16,185,129,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.5) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-5xl px-6 py-16 md:py-20">
        <div className="mb-10 text-center">
          <Motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-4 inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.3em] text-emerald-600">
              <Leaf className="h-3.5 w-3.5" />
              Plans and Pricing
            </span>
            <h1 className="text-3xl font-black leading-tight text-gray-900 md:text-4xl">
              Upgrade for more access to
              <br />
              MaatiTrace satellite intelligence
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-gray-400">
              Cancel anytime. Billing and entitlement enforcement will be
              connected to the backend later.
            </p>
            {authenticated ? (
              <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-white px-4 py-2 text-xs font-bold text-emerald-700 shadow-sm">
                <Check className="h-3.5 w-3.5" />
                Current plan:{" "}
                {
                  PLANS.find(
                    (plan) =>
                      plan.id === currentPlan,
                  )?.name
                }
              </div>
            ) : null}
          </Motion.div>

          <div className="mt-8">
            <BillingToggle
              billing={billing}
              setBilling={setBilling}
            />
          </div>
        </div>

        <div className="mx-auto mb-14 grid max-w-3xl grid-cols-2 gap-3 md:grid-cols-4">
          {TRUST_STATS.map((stat, index) => {
            const Icon = stat.icon;

            return (
              <Motion.div
                key={stat.label}
                initial={{
                  opacity: 0,
                  scale: 0.9,
                }}
                whileInView={{
                  opacity: 1,
                  scale: 1,
                }}
                viewport={{ once: true }}
                transition={{
                  delay: index * 0.08,
                }}
                className="rounded-2xl border border-gray-100 bg-white p-4 text-center"
              >
                <div
                  className={`mx-auto mb-2 flex h-9 w-9 items-center justify-center rounded-xl ${stat.color}`}
                >
                  <Icon
                    className="h-4 w-4"
                    strokeWidth={2.5}
                  />
                </div>
                <p className="text-lg font-black text-gray-900">
                  {stat.value}
                </p>
                <p className="text-[10px] font-medium text-gray-400">
                  {stat.label}
                </p>
              </Motion.div>
            );
          })}
        </div>

        <div className="mx-auto grid max-w-3xl grid-cols-1 gap-6 md:grid-cols-2">
          {PLANS.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              billing={billing}
              authenticated={authenticated}
              currentPlan={currentPlan}
              selectedPlan={selectedPlan}
              onSelect={setSelectedPlan}
            />
          ))}
        </div>

        {/* {authenticated ? (
          <p className="mx-auto mt-4 max-w-3xl rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-center text-xs font-semibold text-amber-800">
            Selection is local UI state only. It does not update your
            account until payment and entitlement backend support is added.
          </p>
        ) : null} */}

        <div className="mt-20">
          <div className="mb-8 text-center">
            <span className="text-[10px] uppercase tracking-[0.3em] text-gray-400">
              Compare every capability
            </span>
            <h2 className="mt-2 text-2xl font-black text-gray-900 md:text-3xl">
              MaatiTrace vs MaatiTrace Pro
            </h2>
          </div>
          <ComparisonTable />
        </div>

        <div className="mt-24">
          <div className="mb-8 text-center">
            <span className="text-[10px] uppercase tracking-[0.3em] text-gray-400">
              Trusted on the ground
            </span>
            <h2 className="mt-2 text-2xl font-black text-gray-900 md:text-3xl">
              What our members say
            </h2>
          </div>
          <div className="mx-auto grid max-w-3xl grid-cols-1 gap-5 md:grid-cols-2">
            {TESTIMONIALS.map((testimonial, index) => (
              <TestimonialCard
                key={testimonial.author}
                testimonial={testimonial}
                index={index}
              />
            ))}
          </div>
        </div>

        <div className="mx-auto mt-24 max-w-2xl">
          <div className="mb-6 text-center">
            <span className="text-[10px] uppercase tracking-[0.3em] text-gray-400">
              Got questions?
            </span>
            <h2 className="mt-2 text-2xl font-black text-gray-900 md:text-3xl">
              Frequently asked
            </h2>
          </div>
          <div className="rounded-3xl border border-gray-100 bg-white px-6 shadow-sm">
            {FAQS.map((faq, index) => (
              <FaqItem
                key={faq.q}
                item={faq}
                index={index}
              />
            ))}
          </div>
        </div>

        <Motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative mt-24 overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-600 via-teal-600 to-emerald-700 px-8 py-12 text-center"
        >
          <div
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage:
                "radial-gradient(circle, white 1px, transparent 1px)",
              backgroundSize: "28px 28px",
            }}
            aria-hidden="true"
          />
          <div className="relative mx-auto max-w-xl space-y-5">
            <h3 className="text-2xl font-black text-white md:text-3xl">
              Start mapping your fields today
            </h3>
            <p className="text-sm leading-relaxed text-emerald-100">
              Join farmers and FPOs using satellite intelligence to
              secure credit, monitor crops and prove land ownership.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link
                to={authenticated ? "/farm-register" : "/register"}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-bold text-emerald-700 shadow-lg transition-all hover:-translate-y-0.5 hover:bg-emerald-50"
              >
                {authenticated
                  ? "Register Land"
                  : "Create Account"}
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to={authenticated ? "/settings" : "/login"}
                className="inline-flex items-center gap-2 rounded-xl border border-white/30 px-6 py-3 text-sm font-medium text-white transition-all hover:bg-white/10"
              >
                {authenticated
                  ? "Open Profile"
                  : "Sign In"}
              </Link>
            </div>
          </div>
        </Motion.div>

        <p className="mx-auto mt-10 max-w-lg text-center text-[10px] leading-relaxed text-gray-300">
          All prices are in Indian Rupees and exclude applicable taxes.
          MaatiTrace stores verification status and masked identifiers
          only.
        </p>
      </div>
    </div>
  );
}

export default function PlansPage() {
  const {
    user,
    isAuthenticated,
  } = useAuth();

  if (isAuthenticated) {
    return (
      <AppShell>
        <PlansContent
          authenticated
          user={user}
        />
      </AppShell>
    );
  }

  return (
    <>
      <PublicNav />
      <div className="pt-28 md:pt-16">
        <PlansContent
          authenticated={false}
          user={null}
        />
      </div>
    </>
  );
}
