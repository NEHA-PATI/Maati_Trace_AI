import * as React from "react";
import { AnimatePresence, motion as Motion } from "framer-motion";

const STAGE_DURATION = 1900;
const IDLE_TIMEOUT = 1000;
const GRADIENT_FROM = [13, 148, 136];
const GRADIENT_TO = [74, 222, 128];

function lerpColor(amount) {
  const red = Math.round(
    GRADIENT_FROM[0]
      + (GRADIENT_TO[0] - GRADIENT_FROM[0]) * amount,
  );
  const green = Math.round(
    GRADIENT_FROM[1]
      + (GRADIENT_TO[1] - GRADIENT_FROM[1]) * amount,
  );
  const blue = Math.round(
    GRADIENT_FROM[2]
      + (GRADIENT_TO[2] - GRADIENT_FROM[2]) * amount,
  );
  return `rgb(${red}, ${green}, ${blue})`;
}

function HexagonBackground({
  hexagonSize = 68,
  hexagonMargin = 3,
  hexRefs,
  onGridChange,
  children,
}) {
  const containerRef = React.useRef(null);
  const hexagonHeight = hexagonSize * 1.1;
  const rowSpacing = hexagonSize * 0.8;
  const computedMarginTop =
    -36 - 0.275 * (hexagonSize - 100) + hexagonMargin;
  const [gridDimensions, setGridDimensions] = React.useState({
    rows: 0,
    columns: 0,
  });

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const updateDimensions = () => {
      const rows = Math.ceil(container.offsetHeight / rowSpacing) + 1;
      const columns = Math.ceil(container.offsetWidth / hexagonSize) + 2;
      setGridDimensions({ rows, columns });
    };

    updateDimensions();
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(updateDimensions);
      observer.observe(container);
      return () => observer.disconnect();
    }

    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, [hexagonSize, rowSpacing]);

  React.useEffect(() => {
    const frame = requestAnimationFrame(onGridChange);
    return () => cancelAnimationFrame(frame);
  }, [gridDimensions, onGridChange]);

  return (
    <div
      ref={containerRef}
      className="relative h-full w-full overflow-hidden bg-stone-100"
    >
      <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
        {Array.from({ length: gridDimensions.rows }).map((_, rowIndex) => (
          <div
            key={`row-${rowIndex}`}
            className="inline-flex"
            style={{
              marginTop: computedMarginTop,
              marginLeft:
                ((rowIndex + 1) % 2 === 0
                  ? hexagonMargin / 2
                  : -(hexagonSize / 2)) - 10,
            }}
          >
            {Array.from({ length: gridDimensions.columns }).map(
              (_, columnIndex) => {
                const key = `${rowIndex}-${columnIndex}`;
                return (
                  <div
                    key={key}
                    ref={(element) => {
                      if (element) hexRefs.current[key] = element;
                      else delete hexRefs.current[key];
                    }}
                    className="mt-hex-cell relative"
                    style={{
                      width: hexagonSize,
                      height: hexagonHeight,
                      marginLeft: hexagonMargin,
                      clipPath:
                        "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
                      "--glow-color": lerpColor(
                        gridDimensions.columns > 1
                          ? columnIndex / (gridDimensions.columns - 1)
                          : 0,
                      ),
                    }}
                  >
                    <div className="absolute inset-0 bg-white" />
                    <div
                      className="mt-hex-inner absolute"
                      style={{
                        inset: hexagonMargin,
                        clipPath:
                          "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)",
                      }}
                    />
                  </div>
                );
              },
            )}
          </div>
        ))}
      </div>
      {children}
    </div>
  );
}

export default function HexagonPipelineLoader({
  open,
  title = "Land registration pipeline",
  steps = [],
  currentStep = 0,
  status = "",
  details = [],
  failure = null,
  warning = null,
  actions = [],
}) {
  const hexRefs = React.useRef({});
  const positionsRef = React.useRef([]);
  const rootRef = React.useRef(null);
  const animationFrameRef = React.useRef(null);
  const mouseRef = React.useRef({ x: -9999, y: -9999 });
  const lastInteractionRef = React.useRef(0);
  const [visualStep, setVisualStep] = React.useState(0);

  const safeCurrentStep = Math.min(
    Math.max(0, currentStep),
    Math.max(0, steps.length - 1),
  );

  React.useEffect(() => {
    if (!open) {
      setVisualStep(0);
      return undefined;
    }

    setVisualStep(safeCurrentStep);
    if (
      safeCurrentStep !== 3
      || !status.toLowerCase().includes("materializing")
    ) {
      return undefined;
    }

    const timer = setInterval(() => {
      setVisualStep((step) => Math.min(step + 1, 6, steps.length - 1));
    }, STAGE_DURATION);
    return () => clearInterval(timer);
  }, [open, safeCurrentStep, status, steps.length]);

  const measure = React.useCallback(() => {
    const root = rootRef.current;
    if (!root) return;
    const rootRect = root.getBoundingClientRect();
    positionsRef.current = Object.values(hexRefs.current).map((element) => {
      const rect = element.getBoundingClientRect();
      return {
        element,
        centerX: rect.left + rect.width / 2 - rootRect.left,
        centerY: rect.top + rect.height / 2 - rootRect.top,
      };
    });
  }, []);

  React.useEffect(() => {
    if (!open) return undefined;
    const startedAt = performance.now();

    const handleMove = (event) => {
      const rect = rootRef.current?.getBoundingClientRect();
      if (!rect) return;
      mouseRef.current = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      lastInteractionRef.current = performance.now();
    };

    const animateGlow = (now) => {
      const rootRect = rootRef.current?.getBoundingClientRect();
      let { x, y } = mouseRef.current;
      let radius = 190;

      if (rootRect && now - lastInteractionRef.current > IDLE_TIMEOUT) {
        radius = Math.max(rootRect.height, 260);
        const phase = (((now - startedAt) / 1000) % 3.2) / 3.2;
        x = rootRect.width * phase;
        y = rootRect.height / 2;
      }

      positionsRef.current.forEach((position) => {
        const distance = Math.hypot(
          position.centerX - x,
          position.centerY - y,
        );
        const glow = Math.max(0, 1 - distance / radius);
        position.element.style.setProperty(
          "--glow",
          glow > 0.02 ? glow.toFixed(3) : "0",
        );
      });
      animationFrameRef.current = requestAnimationFrame(animateGlow);
    };

    window.addEventListener("pointermove", handleMove);
    animationFrameRef.current = requestAnimationFrame(animateGlow);
    return () => {
      window.removeEventListener("pointermove", handleMove);
      cancelAnimationFrame(animationFrameRef.current);
    };
  }, [open]);

  const done = safeCurrentStep >= steps.length - 1 && !failure && !warning;
  const stageLabel = failure
    ? "Pipeline could not be completed"
    : warning
      ? "Analysis completed with warnings"
      : steps[visualStep] || status || "Processing land data";
  const completedSteps = steps.slice(0, visualStep).slice(-2);
  const progress = done
    ? 100
    : Math.round(((visualStep + 1) / Math.max(steps.length, 1)) * 100);

  return (
    <AnimatePresence>
      {open ? (
        <Motion.div
          ref={rootRef}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] h-screen w-screen"
          role="status"
          aria-live="polite"
          aria-label={title}
        >
          <style>{`
            .mt-hex-cell { --glow: 0; }
            .mt-hex-inner {
              background: color-mix(in srgb, #f5f5f4 100%, var(--glow-color, #14b8a6) calc(var(--glow) * 30%));
              box-shadow: 0 0 calc(var(--glow) * 16px) calc(var(--glow) * 1px) color-mix(in srgb, var(--glow-color, #14b8a6) calc(var(--glow) * 55%), transparent);
              transition: box-shadow 300ms ease;
            }
            @keyframes mt-hex-spin { to { transform: rotate(360deg); } }
            .mt-hex-spinner { animation: mt-hex-spin 0.9s linear infinite; }
          `}</style>

          <HexagonBackground
            hexRefs={hexRefs}
            onGridChange={measure}
          >
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center px-6">
              <div className="flex w-full max-w-xl flex-col items-center text-center">
                <p className="mb-8 text-[20px] font-bold uppercase tracking-[0.38em] text-teal-700/70">
                  {title}
                </p>

                <div className="min-h-12">
                  {completedSteps.map((step) => (
                    <Motion.div
                      key={step}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mb-1 flex items-center justify-center gap-2 text-[22px] text-slate-400"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                        <path d="M4 12.5l5 5L20 6" stroke="#14b8a6" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <span>{step}</span>
                    </Motion.div>
                  ))}
                </div>

                <Motion.div
                  key={`${visualStep}-${stageLabel}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-3 flex items-center justify-center gap-3 ${
                    done
                      ? "text-[34px] font-semibold text-teal-700"
                      : failure
                        ? "text-[28px] font-semibold text-rose-700"
                        : warning
                          ? "text-[28px] font-semibold text-amber-700"
                          : "text-[26px] font-medium text-slate-700"
                  }`}
                >
                  {done ? (
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                      <path d="M4 12.5l5 5L20 6" stroke="#14b8a6" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <svg className="mt-hex-spinner" width="17" height="17" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="9" stroke="#cbd5e1" strokeWidth="3" />
                      <path d="M21 12a9 9 0 0 0-9-9" stroke={failure ? "#e11d48" : "#14b8a6"} strokeWidth="3" strokeLinecap="round" />
                    </svg>
                  )}
                  <span>{stageLabel}</span>
                </Motion.div>

                {status && status !== stageLabel && !done ? (
                  <p className="mt-2 text-[22px] text-slate-400">{status}</p>
                ) : null}

                <p className="mt-3 text-[21px] tracking-wide text-slate-400">
                  {warning ? "Completed with warnings" : done ? "Processing complete" : `${progress}% complete`}
                </p>
                <p className="mt-1 text-[15px] font-semibold tracking-wide text-slate-400">
                  Task {done ? steps.length : Math.min(visualStep + 1, steps.length)} of {steps.length}
                </p>

                {details.length ? (
                  <div className="mt-8 flex flex-wrap justify-center gap-2">
                    {details.map((detail) => (
                      <span
                        key={detail}
                        className="rounded-full border border-teal-800/10 bg-white/60 px-3 py-1 text-[20px] font-medium text-slate-500 shadow-sm"
                      >
                        {detail}
                      </span>
                    ))}
                  </div>
                ) : null}
                {actions.length ? (
                  <div className="pointer-events-auto mt-6 flex flex-wrap justify-center gap-2">
                    {actions.map((action) => (
                      <button key={action.label} type="button" onClick={action.onClick} className={`rounded-xl px-4 py-2 text-sm font-semibold ${action.variant === "primary" ? "bg-teal-700 text-white" : "border border-slate-300 bg-white text-slate-700"}`}>
                        {action.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          </HexagonBackground>
        </Motion.div>
      ) : null}
    </AnimatePresence>
  );
}
