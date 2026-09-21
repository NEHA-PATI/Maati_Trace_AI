import React from "react";
import { LandPlot } from "lucide-react";

// Lightweight, dependency-free vector preview of a farm's boundary.
// Draws the real polygon the app already has in memory (no map tiles,
// no extra network calls) so it stays fast on low-end phones and slow data.
const TONES = {
  good: { fill: "var(--mt-leaf-tint)", stroke: "var(--mt-leaf)", text: "var(--mt-leaf-deep)" },
  wait: { fill: "var(--mt-gold-tint)", stroke: "var(--mt-gold)", text: "var(--mt-gold-text)" },
};

export default function FarmPolygonThumb({ polygon = [], tone = "good", className = "" }) {
  const colors = TONES[tone] || TONES.good;
  const points = Array.isArray(polygon)
    ? polygon.filter((point) => Array.isArray(point) && point.length === 2 && Number.isFinite(point[0]) && Number.isFinite(point[1]))
    : [];

  if (points.length < 3) {
    return (
      <div className={className} style={{ background: colors.fill }}>
        <div className="flex h-full w-full items-center justify-center">
          <LandPlot className="h-7 w-7" style={{ color: colors.stroke }} strokeWidth={1.8} />
        </div>
      </div>
    );
  }

  const lats = points.map((point) => point[0]);
  const lngs = points.map((point) => point[1]);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  const W = 200;
  const H = 120;
  const PAD = 14;
  const spanLat = Math.max(maxLat - minLat, 1e-6);
  const spanLng = Math.max(maxLng - minLng, 1e-6);
  const scale = Math.min((W - PAD * 2) / spanLng, (H - PAD * 2) / spanLat);
  const offX = (W - spanLng * scale) / 2;
  const offY = (H - spanLat * scale) / 2;

  const svgPoints = points
    .map(([lat, lng]) => {
      const x = offX + (lng - minLng) * scale;
      const y = H - (offY + (lat - minLat) * scale); // flip: latitude increases upward
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className={className} style={{ background: colors.fill }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Farm boundary shape">
        <polygon
          points={svgPoints}
          fill={colors.stroke}
          fillOpacity="0.32"
          stroke={colors.stroke}
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
