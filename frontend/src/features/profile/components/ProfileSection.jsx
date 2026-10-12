import {
  forwardRef,
  useEffect,
  useRef,
  useState,
} from "react";
import { AlertCircle } from "lucide-react";

export function ProfileGrid({
  children,
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {children}
    </div>
  );
}

export function FieldError({
  error,
}) {
  if (!error?.message) {
    return null;
  }

  return (
    <p className="mt-scale-in mt-1.5 flex items-center gap-1.5 text-xs font-semibold text-[color:var(--mt-rose)]">
      <AlertCircle className="h-3.5 w-3.5" />
      {error.message}
    </p>
  );
}

export function FieldLabel({
  children,
  required = false,
}) {
  return (
    <span className="mt-font-mono mb-1.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#7F8D79]">
      {children}
      {required ? (
          <span className="rounded-full bg-[#FFF3D8] px-2 py-0.5 text-[9px] font-bold tracking-[0.1em] text-[#8A6729]">
          Required
        </span>
      ) : null}
    </span>
  );
}

const fieldSurface =
  "w-full rounded-xl border border-[#E3E8DE] bg-[#F8FAF6] px-3.5 py-3 text-sm text-[#1D2117] outline-none transition-all duration-200 ease-out placeholder:text-[#9AA397] focus:-translate-y-[1px] focus:border-[#7FA66A] focus:bg-white focus:shadow-[0_0_0_4px_rgba(127,166,106,0.14)] hover:border-[#C9D8BD]";

export const ProfileInput = forwardRef(
  function ProfileInput(
    {
      label,
      error,
      required = false,
      className = "",
      ...props
    },
    ref,
  ) {
    return (
      <label className={`block ${className}`}>
        <FieldLabel required={required}>
          {label}
        </FieldLabel>
        <input
          {...props}
          ref={ref}
          className={fieldSurface}
        />
        <FieldError error={error} />
      </label>
    );
  },
);

export const ProfileTextarea = forwardRef(
  function ProfileTextarea(
    {
      label,
      error,
      required = false,
      className = "",
      ...props
    },
    ref,
  ) {
    return (
      <label className={`block ${className}`}>
        <FieldLabel required={required}>
          {label}
        </FieldLabel>
        <textarea
          {...props}
          ref={ref}
          className={`min-h-28 resize-y ${fieldSurface}`}
        />
        <FieldError error={error} />
      </label>
    );
  },
);

export const ProfileSelect = forwardRef(
  function ProfileSelect(
    {
      label,
      error,
      required = false,
      children,
      className = "",
      ...props
    },
    ref,
  ) {
    return (
      <label className={`block ${className}`}>
        <FieldLabel required={required}>
          {label}
        </FieldLabel>
        <select
          {...props}
          ref={ref}
          className={`cursor-pointer ${fieldSurface}`}
        >
          {children}
        </select>
        <FieldError error={error} />
      </label>
    );
  },
);

export const ProfileCheckbox = forwardRef(
  function ProfileCheckbox(
    {
      label,
      description,
      error,
      ...props
    },
    ref,
  ) {
    return (
      <label className="group flex cursor-pointer gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4 text-sm transition-all duration-200 hover:border-[color:var(--mt-forest)]/40 hover:bg-white">
        <input
          {...props}
          ref={ref}
          type="checkbox"
          className="mt-1 h-4 w-4 rounded border-slate-300 text-[color:var(--mt-forest)] accent-[color:var(--mt-forest)] transition-transform duration-150 checked:scale-110"
        />
        <span>
          <span className="block font-bold text-slate-900">
            {label}
          </span>
          {description ? (
            <span className="mt-1 block text-xs leading-5 text-slate-500">
              {description}
            </span>
          ) : null}
          <FieldError error={error} />
        </span>
      </label>
    );
  },
);

export function ReadOnlyValue({
  label,
  value,
}) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <div className="mt-font-mono flex items-center justify-between rounded-xl border border-dashed border-[#CCD8C7] bg-[#F8FAF6] px-3.5 py-3 text-sm font-semibold text-[#687064]">
        {value || "Not available"}
      </div>
    </div>
  );
}

export function ProfileSection({
  id,
  icon: Icon,
  title,
  eyebrow,
  children,
}) {
  const ref = useRef(null);
  const [visible, setVisible] =
    useState(false);

  useEffect(() => {
    const node = ref.current;

    if (!node) {
      return undefined;
    }

    if (
      typeof IntersectionObserver
      === "undefined"
    ) {
      setVisible(true);
      return undefined;
    }

    const observer =
      new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
          }
        },
        {
          threshold: 0.08,
          rootMargin:
            "0px 0px -60px 0px",
        },
      );

    observer.observe(node);

    return () =>
      observer.disconnect();
  }, []);

  return (
    <section
      id={id}
      ref={ref}
      className={`group/section scroll-mt-24 overflow-hidden rounded-[1.5rem] border border-[#E3E8DE] bg-white shadow-[0_4px_14px_rgba(43,61,35,0.04)] transition-all duration-300 hover:shadow-[0_18px_50px_rgba(43,61,35,0.08)] ${
        visible
          ? "mt-reveal mt-reveal-in"
          : "mt-reveal"
      }`}
    >
      <div className="relative border-b border-[#E9EDE5] bg-gradient-to-r from-[#F7FAF4] to-white px-5 py-4">
        <span
          className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-[color:var(--mt-forest)] to-[color:var(--mt-harvest)] opacity-0 transition-opacity duration-300 group-hover/section:opacity-100"
          aria-hidden="true"
        />
        <div className="flex items-center gap-3">
          {Icon ? (
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#4B6B3A] shadow-[0_6px_16px_rgba(75,107,58,0.2)] transition-transform duration-300 group-hover/section:scale-105">
              <Icon className="h-5 w-5 text-white" />
            </div>
          ) : null}
          <div>
            {eyebrow ? (
              <p className="mt-font-mono text-[10px] font-semibold uppercase tracking-[0.26em] text-[#9A762D]">
                {eyebrow}
              </p>
            ) : null}
            <h2 className="mt-font-display text-lg font-semibold text-[#1D2117]">
              {title}
            </h2>
          </div>
        </div>
      </div>
      <div className="space-y-5 p-5">
        {children}
      </div>
    </section>
  );
}
