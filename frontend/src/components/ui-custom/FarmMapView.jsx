import React, { useState } from "react";
import { motion } from "framer-motion";

// A static satellite-imagery map with SVG polygon overlay + grid + NDVI labels
// Mimics the reference image: satellite bg, black grid lines, red dashed polygon, green % labels

const GRID_COLS = 8;
const GRID_ROWS = 8;

// Polygon points as % of container (mimics irregular farm boundary)
const POLYGON_POINTS = [
  [18, 8], [55, 4], [82, 12], [88, 42], [80, 78],
  [58, 88], [28, 84], [10, 65], [8, 38]
];

// Which cells are inside the polygon (approximate)
const INSIDE_CELLS = new Set([
  "1-1","1-2","1-3","1-4","1-5",
  "2-1","2-2","2-3","2-4","2-5","2-6",
  "3-0","3-1","3-2","3-3","3-4","3-5","3-6",
  "4-0","4-1","4-2","4-3","4-4","4-5","4-6","4-7",
  "5-1","5-2","5-3","5-4","5-5","5-6","5-7",
  "6-1","6-2","6-3","6-4","6-5","6-6",
  "7-2","7-3","7-4","7-5","7-6",
]);

// Seed NDVI values per inside-cell so they don't change on re-render
const CELL_NDVI = {};
const SEED = [94, 38, 65, 56, 24, 97, 88, 67, 72, 81, 45, 63, 58, 79, 33, 86, 71, 49, 90, 55, 68, 42, 77, 35, 83];
let si = 0;
for (const k of INSIDE_CELLS) { CELL_NDVI[k] = SEED[si++ % SEED.length]; }

function pointsToSvg(pts, w, h) {
  return pts.map(([px, py]) => `${(px / 100) * w},${(py / 100) * h}`).join(" ");
}

export default function FarmMapView({ farm }) {
  const [hovered, setHovered] = useState(null);
  const W = 560, H = 400;

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-gray-200 shadow-lg" style={{ fontFamily: "'Poppins', sans-serif" }}>
      {/* Satellite image base */}
      <div className="relative" style={{ paddingBottom: `${(H / W) * 100}%` }}>
        <img
          src="https://res.cloudinary.com/dkst917dg/image/upload/v1780464229/31_h2wcys.jpg"
          alt="Satellite view"
          className="absolute inset-0 w-full h-full object-cover"
        />

        {/* SVG overlay */}
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="xMidYMid slice"
        >
          {/* Black grid lines */}
          {Array.from({ length: GRID_COLS + 1 }).map((_, c) => (
            <line key={`vc${c}`} x1={(c / GRID_COLS) * W} y1={0} x2={(c / GRID_COLS) * W} y2={H}
              stroke="rgba(0,0,0,0.55)" strokeWidth="1" />
          ))}
          {Array.from({ length: GRID_ROWS + 1 }).map((_, r) => (
            <line key={`hr${r}`} x1={0} y1={(r / GRID_ROWS) * H} x2={W} y2={(r / GRID_ROWS) * H}
              stroke="rgba(0,0,0,0.55)" strokeWidth="1" />
          ))}

          {/* Farm polygon — red dashed border */}
          <polygon
            points={pointsToSvg(POLYGON_POINTS, W, H)}
            fill="rgba(220,50,50,0.08)"
            stroke="#ff3333"
            strokeWidth="2.5"
            strokeDasharray="8,5"
            strokeLinejoin="round"
          />

          {/* NDVI % labels on inside cells */}
          {Array.from(INSIDE_CELLS).map(key => {
            const [r, c] = key.split("-").map(Number);
            const cx = ((c + 0.5) / GRID_COLS) * W;
            const cy = ((r + 0.5) / GRID_ROWS) * H;
            const val = CELL_NDVI[key];
            const isHov = hovered === key;
            return (
              <g key={key}
                onMouseEnter={() => setHovered(key)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: "pointer" }}
              >
                {isHov && (
                  <rect
                    x={((c) / GRID_COLS) * W + 1}
                    y={((r) / GRID_ROWS) * H + 1}
                    width={W / GRID_COLS - 2}
                    height={H / GRID_ROWS - 2}
                    fill="rgba(255,255,255,0.18)"
                    rx="2"
                  />
                )}
                <text
                  x={cx} y={cy + 5}
                  textAnchor="middle"
                  fontSize="13"
                  fontWeight="700"
                  fontFamily="Poppins, sans-serif"
                  fill={val > 70 ? "#22c55e" : val > 45 ? "#86efac" : "#fbbf24"}
                  style={{ textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}
                  filter="url(#shadow)"
                >
                  {val}%
                </text>
              </g>
            );
          })}

          {/* Drop shadow filter for text */}
          <defs>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="1" stdDeviation="1.5" floodColor="rgba(0,0,0,0.9)" />
            </filter>
          </defs>
        </svg>

        {/* Zoom controls (cosmetic) */}
        <div className="absolute bottom-3 right-3 flex flex-col gap-1">
          <button className="w-7 h-7 bg-gray-900/80 text-white rounded-md text-lg font-bold leading-none flex items-center justify-center hover:bg-gray-800 transition-colors">+</button>
          <button className="w-7 h-7 bg-gray-900/80 text-white rounded-md text-lg font-bold leading-none flex items-center justify-center hover:bg-gray-800 transition-colors">−</button>
        </div>

        {/* Farm ID badge */}
        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-sm text-white text-[11px] font-semibold px-3 py-1 rounded-full">
          {farm?.id || "MF-0042"} · {farm?.area || 2.4} ha
        </div>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5 flex items-center gap-3">
          <span className="flex items-center gap-1 text-[10px] text-green-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-green-400 inline-block" /> High NDVI
          </span>
          <span className="flex items-center gap-1 text-[10px] text-yellow-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" /> Low NDVI
          </span>
        </div>
      </div>
    </div>
  );
}