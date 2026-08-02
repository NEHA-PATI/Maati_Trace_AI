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
          stroke="rgba(255,255,255,0.18)"
          strokeWidth={STROKE}
        />
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="#c1852f"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={
            CIRCUMFERENCE
          }
          strokeDashoffset={offset}
          style={{
            transition:
              "stroke-dashoffset 1.1s cubic-bezier(0.16,1,0.3,1)",
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <Sprout className="h-3.5 w-3.5 text-lime-200/90" />
        <span className="mt-font-display text-lg font-semibold leading-none text-white">
          {clamped}%
        </span>
      </div>
    </div>
  );
}
