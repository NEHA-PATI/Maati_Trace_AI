import {
  useEffect,
  useState,
} from "react";
import {
  CheckCircle2,
  Download,
  Save,
} from "lucide-react";

export function ProfileControls({
  saving,
  exporting,
  savedAt,
  onExport,
}) {
  const [justSaved, setJustSaved] =
    useState(false);

  useEffect(() => {
    if (!savedAt) {
      return undefined;
    }

    setJustSaved(true);
    const timeout = setTimeout(
      () => setJustSaved(false),
      2200,
    );

    return () =>
      clearTimeout(timeout);
  }, [savedAt]);

  return (
    <div className="mt-fade-up sticky bottom-4 z-20 flex flex-col gap-3 rounded-[1.5rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_60px_rgba(15,23,42,0.14)] backdrop-blur-md transition-shadow duration-300 md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-3">
        {justSaved ? (
          <span
            className="mt-pop flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[color:var(--mt-forest-soft)]"
            aria-hidden="true"
          >
            <CheckCircle2 className="h-5 w-5 text-[color:var(--mt-forest)]" />
          </span>
        ) : null}
        <div>
          <p className="mt-font-display text-sm font-semibold text-slate-950">
            {justSaved
            ? "Profile saved"
            : "Review your changes"}
          </p>
          <p className="text-xs leading-5 text-slate-500">
            Only changed editable fields are sent to the backend.
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onExport}
          disabled={exporting}
          className="relative inline-flex h-11 items-center gap-2 overflow-hidden rounded-2xl border border-slate-200 bg-white px-5 text-sm font-bold text-slate-700 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-60"
        >
          {exporting ? (
            <span
              className="mt-shimmer absolute inset-0"
              aria-hidden="true"
            />
          ) : null}
          <Download className="h-4 w-4" />
          {exporting
            ? "Exporting..."
            : "Export JSON"}
        </button>
        <button
          type="submit"
          disabled={saving}
          className="relative inline-flex h-11 items-center gap-2 overflow-hidden rounded-2xl bg-[color:var(--mt-forest-deep)] px-5 text-sm font-bold text-white shadow-[0_10px_24px_rgba(18,51,31,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[color:var(--mt-forest)] disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-70"
        >
          {saving ? (
            <span
              className="mt-shimmer absolute inset-0"
              aria-hidden="true"
            />
          ) : null}
          <Save className="h-4 w-4" />
          {saving
            ? "Saving..."
            : "Save profile"}
        </button>
      </div>
    </div>
  );
}
