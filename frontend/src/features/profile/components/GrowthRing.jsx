import {
  useEffect,
  useState,
} from "react";
import { Sprout } from "lucide-react";

const SIZE = 84;
const STROKE = 7;
const RADIUS =
  (SIZE - STROKE) / 2;
const CIRCUMFERENCE =
  2 * Math.PI * RADIUS;

export function GrowthRing({
  value = 0,
}) {
  const clamped = Math.max(
    0,
    Math.min(100, value),
  );
  const [drawn, setDrawn] =
    useState(0);

  useEffect(() => {
    const frame =
      requestAnimationFrame(() => {
        setDrawn(clamped);
      });

    return () =>
      cancelAnimationFrame(frame);
  }, [clamped]);

  const offset =
    CIRCUMFERENCE
    - (drawn / 100)
      * CIRCUMFERENCE;

  return (
    <div className="relative flex h-[84px] w-[84px] items-center justify-center">
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="-rotate-90"
      >
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="rgb(16 185 129 / 15%)"
          strokeWidth={STROKE}
        />
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="#10b981"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={
            CIRCUMFERENCE
          }
          strokeDashoffset={offset}
          style={{
            filter:
              "drop-shadow(0 0 4px rgba(16,185,129,0.4))",
            transition:
              "stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)",
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <Sprout className="h-3.5 w-3.5 text-emerald-500" />
        <span className="mt-font-display mt-0.5 text-lg font-semibold leading-none text-slate-900">
          {clamped}%
        </span>
      </div>
    </div>
  );
}
