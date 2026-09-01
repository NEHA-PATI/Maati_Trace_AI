import React from "react";
import { Link } from "react-router-dom";
import { Droplets, CloudSun, MapPin, ChevronRight } from "lucide-react";

const PRIORITY_STYLES = {
  high: {
    bar: "before:bg-[var(--mt-clay)]",
    icon: "bg-[var(--mt-clay-tint)] text-[var(--mt-clay-text)]",
    Icon: Droplets,
  },
  medium: {
    bar: "before:bg-[var(--mt-gold)]",
    icon: "bg-[var(--mt-gold-tint)] text-[var(--mt-gold-text)]",
    Icon: CloudSun,
  },
  low: {
    bar: "before:bg-[var(--mt-leaf)]",
    icon: "bg-[var(--mt-leaf-tint)] text-[var(--mt-leaf-deep)]",
    Icon: MapPin,
  },
};

const DEMO_NOTIFICATIONS = [
  { id: 1, priority: "high", title: "Soil water is low", detail: "Farm MF-0042 in Puri needs water soon. Please check the field.", time: "12 minutes ago", farmId: "MF-0042" },
  { id: 2, priority: "high", title: "Sky too cloudy to check", detail: "Your Nayagarh farm could not be checked from the sky today.", time: "1 hour ago", farmId: null },
  { id: 3, priority: "medium", title: "A new farm was added", detail: "Ramesh Sahoo added a new farm in Khurda block.", time: "3 hours ago", farmId: "MF-0089" },
  { id: 4, priority: "medium", title: "Farm check finished", detail: "Batch 12 — 34 farms checked, 2 need another look.", time: "5 hours ago", farmId: null },
  { id: 5, priority: "low", title: "New sky picture ready", detail: "A fresh satellite picture from 15 Jan is ready for Puri district.", time: "8 hours ago", farmId: null },
];

export default function NotificationStack({ limit = 5, showAll = false }) {
  const notifications = showAll ? DEMO_NOTIFICATIONS : DEMO_NOTIFICATIONS.slice(0, limit);

  return (
    <div className="mt-surface space-y-2.5 p-1">
      {notifications.map((n) => {
        const style = PRIORITY_STYLES[n.priority];
        const Icon = style.Icon;
        return (
          <div
            key={n.id}
            className={`relative flex gap-3 overflow-hidden rounded-[var(--mt-radius-md)] border border-[var(--mt-line)] bg-white p-3.5 before:absolute before:inset-y-0 before:left-0 before:w-1 before:content-[''] ${style.bar}`}
          >
            <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${style.icon}`}>
              <Icon className="h-4 w-4" strokeWidth={2.2} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[14px] font-extrabold leading-tight text-[var(--mt-ink)]">{n.title}</p>
              <p className="mt-1 text-[12.5px] font-semibold leading-snug text-[var(--mt-ink-soft)]">{n.detail}</p>
              <p className="mt-1.5 text-[11px] font-semibold text-[var(--mt-ink-faint)]">{n.time}</p>
            </div>
            {n.farmId && (
              <Link
                to={`/land/${n.farmId}`}
                aria-label={`Open ${n.title}`}
                className="flex h-11 w-11 shrink-0 items-center justify-center self-center rounded-full text-[var(--mt-leaf-deep)] hover:bg-[var(--mt-leaf-tint)]"
              >
                <ChevronRight className="h-4 w-4" strokeWidth={2.6} />
              </Link>
            )}
          </div>
        );
      })}
    </div>
  );
}
