import React from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Info, CheckCircle, ChevronRight } from "lucide-react";

const PRIORITY_ICONS = {
  high: AlertTriangle,
  medium: Info,
  low: CheckCircle,
};

const PRIORITY_STYLES = {
  high: "border-l-destructive bg-destructive/5",
  medium: "border-l-amber-500 bg-amber-500/5",
  low: "border-l-primary bg-primary/5",
};

const DEMO_NOTIFICATIONS = [
  { id: 1, priority: "high", title: "Moisture Stress Detected", detail: "Farm MF-0042 — Puri Block, NDVI dropped below 0.3", time: "12 min ago", farmId: "MF-0042" },
  { id: 2, priority: "high", title: "Cloud Cover Warning", detail: "Satellite scene for Nayagarh — 78% cloud cover, scene unusable", time: "1 hr ago", farmId: null },
  { id: 3, priority: "medium", title: "New Farm Registered", detail: "Farmer Ramesh Sahoo added Farm MF-0089 in Khurda Block", time: "3 hrs ago", farmId: "MF-0089" },
  { id: 4, priority: "medium", title: "Raster Processing Complete", detail: "Batch 12 — 34 farms processed, 2 failed cloud validation", time: "5 hrs ago", farmId: null },
  { id: 5, priority: "low", title: "Satellite Scene Available", detail: "Sentinel-2 scene dated 2025-01-15 available for Puri district", time: "8 hrs ago", farmId: null },
];

export default function NotificationStack({ limit = 5, showAll = false }) {
  const notifications = showAll ? DEMO_NOTIFICATIONS : DEMO_NOTIFICATIONS.slice(0, limit);

  return (
    <div className="space-y-1">
      {notifications.map((n) => {
        const Icon = PRIORITY_ICONS[n.priority];
        return (
          <div key={n.id} className={`border-l-2 ${PRIORITY_STYLES[n.priority]} px-3 py-2.5 rounded-r-sm relative`}>
            {n.priority === "high" && (
              <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-destructive pulse-live" />
            )}
            <div className="flex items-start gap-2">
              <Icon className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${n.priority === "high" ? "text-destructive" : n.priority === "medium" ? "text-amber-600" : "text-primary"}`} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-display font-semibold text-foreground leading-tight">{n.title}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5 leading-snug">{n.detail}</p>
                <p className="text-[9px] text-muted-foreground/60 mt-1 font-display uppercase tracking-wider">{n.time}</p>
              </div>
              {n.farmId && (
                <Link to={`/land/${n.farmId}`} className="text-primary hover:underline">
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
