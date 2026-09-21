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
      "Essential satellite-based crop monitoring for small and individual farmers.",
    storage: {
      icon: Cloud,
      value: "Up to 1 acre",
    },
    monthly: 0,
    annual: 0,
    cta: "Start Free",
    ctaTo: "/register",
    audience: "Individual Farmers",
    highlights: [
      {
        icon: MapPin,
        label: "Farm registration up to 1 acre",
      },
      {
        icon: Satellite,
        label: "Satellite imagery analysis",
      },
    ],
    features: [
      {
        icon: MapPin,
        title: "Farm registration up to 1 acre",
        desc: "Register and map one farm with a total area of up to 1 acre.",
      },
      {
        icon: Satellite,
        title: "Satellite imagery analysis",
        desc: "Monitor farm conditions using processed satellite imagery.",
      },
      {
        icon: Leaf,
        title: "Crop Greenness",
        desc: "Understand how green and healthy the crop appears.",
      },
      {
        icon: TrendingUp,
        title: "Crop Growth",
        desc: "Track the overall strength and development of crop growth.",
      },
      {
        icon: Sparkles,
        title: "Early Crop Growth",
        desc: "Monitor crop establishment during the early growth stage.",
      },
      {
        icon: Cloud,
        title: "Crop Moisture",
        desc: "Identify moisture conditions within the crop vegetation.",
      },
      {
        icon: Database,
        title: "Water Availability",
        desc: "Understand the level of water available in the farm.",
      },
      {
        icon: Zap,
        title: "Water Stress",
        desc: "Detect signs of crop stress caused by insufficient water.",
      },
      {
        icon: Leaf,
        title: "Crop Nutrition",
        desc: "Identify possible changes in crop nutrient condition.",
      },
      {
        icon: Layers,
        title: "Bare Land",
        desc: "Detect areas where soil is exposed or vegetation is absent.",
      },
      {
        icon: BarChart3,
        title: "Crop Condition",
        desc: "View the overall condition of crops across the registered farm.",
      },
    ],
  },
  {
    id: "maatitrace_pro",
    name: "MaatiTrace Pro",
    tagline:
      "Advanced farm intelligence with actionable crop recommendations and alerts.",
    storage: {
      icon: Cloud,
      value: "Charged per acre",
    },
    monthly: 100,
    annual: 100,
    cta: "Get MaatiTrace Pro",
    ctaTo: "/register",
    recommended: true,
    audience: "Farmers and FPOs",
    highlights: [
      {
        icon: TrendingUp,
        label: "\u20B9100 per acre",
      },
      {
        icon: Sparkles,
        label: "Advanced analytics",
      },
    ],
    features: [
      {
        icon: Sparkles,
        title: "MaatiTrace Advanced Analytics",
        desc: "Access advanced satellite-based farm and crop analytics.",
      },
      {
        icon: BarChart3,
        title: "Crop Insights",
        desc: "Receive clear insights about crop growth, health and field condition.",
      },
      {
        icon: Zap,
        title: "Crop Stress Detection",
        desc: "Detect possible water, moisture and vegetation stress early.",
      },
      {
        icon: Leaf,
        title: "Fertilizer Recommendation",
        desc: "Receive fertilizer guidance based on crop and farm conditions.",
      },
      {
        icon: Shield,
        title: "Pesticide Alerts",
        desc: "Receive alerts when crop conditions indicate possible pest risk.",
      },
      {
        icon: TrendingUp,
        title: "Yield Insights",
        desc: "View expected crop yield and changes in yield potential.",
      },
    ],
  },
];

const COMPARE_ROWS = [
  {
    feature: "Pricing",
    icon: BarChart3,
    basic: "Free",
    pro: "\u20B9100 per acre",
  },
  {
    feature: "Farm registration",
    icon: MapPin,
    basic: "Up to 1 acre",
    pro: "Based on paid acreage",
  },
  {
    feature: "Satellite imagery analysis",
    icon: Satellite,
    basic: true,
    pro: true,
  },
  {
    feature: "Crop Greenness",
    icon: Leaf,
    basic: true,
    pro: true,
  },
  {
    feature: "Crop Growth",
    icon: TrendingUp,
    basic: true,
    pro: true,
  },
  {
    feature: "Early Crop Growth",
    icon: Sparkles,
    basic: true,
    pro: true,
  },
  {
    feature: "Crop Moisture",
    icon: Cloud,
    basic: true,
    pro: true,
  },
  {
    feature: "Water Availability",
    icon: Database,
    basic: true,
    pro: true,
  },
  {
    feature: "Water Stress",
    icon: Zap,
    basic: true,
    pro: true,
  },
  {
    feature: "Crop Nutrition",
    icon: Leaf,
    basic: true,
    pro: true,
  },
  {
    feature: "Bare Land",
    icon: Layers,
    basic: true,
    pro: true,
  },
  {
    feature: "Crop Condition",
    icon: BarChart3,
    basic: true,
    pro: true,
  },
  {
    feature: "Advanced Analytics",
    icon: Sparkles,
    basic: false,
    pro: true,
  },
  {
    feature: "Crop Insights",
    icon: BarChart3,
    basic: false,
    pro: true,
  },
  {
    feature: "Crop Stress Detection",
    icon: Zap,
    basic: false,
    pro: true,
  },
  {
    feature: "Fertilizer Recommendation",
    icon: Leaf,
    basic: false,
    pro: true,
  },
  {
    feature: "Pesticide Alerts",
    icon: Shield,
    basic: false,
    pro: true,
  },
  {
    feature: "Yield Insights",
    icon: TrendingUp,
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
      "I registered my one-acre farm for free and started monitoring crop conditions from one place.",
    author: "Ramesh Sahoo",
    role: "Smallholder Farmer, Odisha",
    accent: "bg-blue-500",
  },
];

const FAQS = [
  {
    q: "Is MaatiTrace really free for individual farmers?",
    a: "Yes. The free tier supports registration and satellite imagery analysis for one farm with a total area of up to 1 acre.",
  },
  {
    q: "How are Pro plans billed?",
    a: "MaatiTrace Pro is charged at \u20B9100 per registered acre. Applicable taxes and payment processing will be handled when backend billing is connected.",
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
    a: "Yes. MaatiTrace Pro is intended for both farmers and FPOs that need advanced crop insights, alerts and recommendations across paid acreage.",
  },
];

function normalizePlanId(plan) {
  if (plan === "pro" || plan === "maatitrace_pro") {
    return "maatitrace_pro";
  }

  return "maatitrace";
}

function PlanCard({
  plan,
  authenticated,
  currentPlan,
  selectedPlan,
  onSelect,
}) {
  const StorageIcon = plan.storage.icon;
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
            {plan.id === "maatitrace"
              ? "Free"
              : `\u20B9${plan.monthly.toLocaleString("en-IN")}`}
          </span>
          {plan.id === "maatitrace_pro" ? (
            <span className="text-sm font-medium text-gray-400">
              /acre
            </span>
          ) : null}
        </div>

        <p className="mb-1 text-xs text-gray-400">
          {plan.id === "maatitrace"
            ? "Free for farm registration up to 1 acre"
            : "Pay only for the registered farm area"}
        </p>

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
                  {"\u20B9"}100 per acre
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

      <div className="relative mx-auto max-w-7xl px-5 py-16 sm:px-8 md:py-20 lg:px-10">
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
              Start free with one acre, then unlock advanced intelligence at
              a simple per-acre price.
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
        </div>

        {/* <div className="mx-auto mb-14 grid max-w-3xl grid-cols-2 gap-3 md:grid-cols-4">
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
        </div> */}

        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-8 lg:grid-cols-2">
          {PLANS.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
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

        {/* <div className="mt-24">
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
        </div> */}

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
