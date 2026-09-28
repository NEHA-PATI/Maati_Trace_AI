import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, FileUp, ShieldCheck } from "lucide-react";
import FpoFeatureGate from "../access/FpoFeatureGate";
import {
  commitFpoImport,
  createFpoImportIntent,
  getFpoImportRows,
  getFpoImports,
  getFpoImportTemplate,
  getFpoStagedImportRecords,
  uploadFpoImportContent,
  validateFpoImport,
} from "../api/fpoPortalApi";

async function checksum(file) {
  return [
    ...new Uint8Array(
      await crypto.subtle.digest("SHA-256", await file.arrayBuffer()),
    ),
  ]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export default function FpoImportsPage() {
  const [type, setType] = useState("FARMERS");
  const [file, setFile] = useState(null);
  const [selected, setSelected] = useState(null);
  const [message, setMessage] = useState("");
  const qc = useQueryClient();
  const jobs = useQuery({ queryKey: ["fpo-imports"], queryFn: getFpoImports });
  const rows = useQuery({
    queryKey: ["fpo-import-rows", selected],
    queryFn: () => getFpoImportRows(selected),
    enabled: Boolean(selected),
  });
  const staged = useQuery({
    queryKey: ["fpo-staged-import-records", selected],
    queryFn: () => getFpoStagedImportRecords(selected),
    enabled: Boolean(selected),
  });
  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Choose a CSV or XLSX file first.");
      const sum = await checksum(file);
      const format = file.name.toLowerCase().endsWith(".xlsx") ? "XLSX" : "CSV";
      const intent = await createFpoImportIntent({
        import_type: type,
        source_format: format,
        filename: file.name,
        checksum: sum,
      });
      await uploadFpoImportContent(intent.import_job_id, file);
      await validateFpoImport(intent.import_job_id);
      return intent.import_job_id;
    },
    onSuccess: (id) => {
      setSelected(id);
      setMessage("Dry run complete. Review every row before any commit.");
      qc.invalidateQueries({ queryKey: ["fpo-imports"] });
      qc.invalidateQueries({ queryKey: ["fpo-import-rows", id] });
      qc.invalidateQueries({ queryKey: ["fpo-staged-import-records", id] });
    },
  });
  const commit = useMutation({
    mutationFn: () => commitFpoImport(selected),
    onSuccess: () => {
      setMessage(
        "Commit queued. Valid rows will be staged for farmer account, farm confirmation, and consent steps.",
      );
      qc.invalidateQueries({ queryKey: ["fpo-imports"] });
      qc.invalidateQueries({
        queryKey: ["fpo-staged-import-records", selected],
      });
    },
  });
  const invalid = useMemo(
    () => (rows.data || []).filter((row) => row.row_status === "INVALID"),
    [rows.data],
  );

  async function downloadTemplate() {
    const template = await getFpoImportTemplate(type);
    const csv = `${template.columns.join(",")}\n`;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8" }),
    );
    link.download = `maati-${type.toLowerCase()}-template-v${template.template_version}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
  return (
    <FpoFeatureGate
      feature="BULK_FARM_REGISTRATION"
      fallback={
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-8">
          <h1 className="text-2xl font-black text-amber-950">
            Bulk onboarding is not enabled
          </h1>
          <p className="mt-2 text-sm text-amber-800">
            Your current FPO plan does not include controlled imports.
          </p>
        </section>
      }
    >
      <div className="space-y-6">
        <header>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-700">
            Class B · Growth operations
          </p>
          <h1 className="mt-2 text-3xl font-black text-slate-950">
            Bulk onboarding
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Upload a versioned CSV or XLSX, verify the checksum, run a dry
            validation, and inspect row-level outcomes before downstream records
            are created. Enter crop names; MaatiTrace resolves the canonical
            crop code automatically.
          </p>
        </header>
        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <FileUp className="h-5 w-5 text-emerald-700" />
            <p className="mt-4 text-sm font-black">1. Upload</p>
            <p className="mt-1 text-xs text-slate-500">
              CSV/XLSX template, 5,000 rows maximum. No farmer ID is entered.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <ShieldCheck className="h-5 w-5 text-emerald-700" />
            <p className="mt-4 text-sm font-black">2. Dry run</p>
            <p className="mt-1 text-xs text-slate-500">
              Formula cells and missing fields are rejected.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <CheckCircle2 className="h-5 w-5 text-emerald-700" />
            <p className="mt-4 text-sm font-black">3. Review</p>
            <p className="mt-1 text-xs text-slate-500">
              No partial commit is hidden behind a success toast.
            </p>
          </div>
        </section>
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="flex flex-wrap items-end gap-4">
            <label className="text-sm font-bold text-slate-700">
              Import type
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="mt-2 block rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option>FARMERS</option>
                <option>FARMS</option>
                <option>FARMERS_AND_FARMS</option>
              </select>
            </label>
            <button
              type="button"
              onClick={() =>
                downloadTemplate().catch((error) =>
                  setMessage(
                    error?.message || "Template could not be downloaded.",
                  ),
                )
              }
              className="rounded-xl border border-emerald-200 px-4 py-2.5 text-sm font-black text-emerald-800 hover:bg-emerald-50"
            >
              Download template
            </button>
            <label className="text-sm font-bold text-slate-700">
              CSV or XLSX file
              <input
                type="file"
                accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="mt-2 block max-w-xs text-sm"
              />
            </label>
            <button
              onClick={() => upload.mutate()}
              disabled={upload.isPending || !file}
              className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {upload.isPending ? "Validating…" : "Run dry validation"}
            </button>
          </div>
          {message && (
            <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
              {message}
            </p>
          )}
          {upload.isError && (
            <p className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">
              {upload.error.message}
            </p>
          )}
        </section>
        <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-6">
            <h2 className="font-black">Import history</h2>
            <div className="mt-4 space-y-2">
              {(jobs.data || []).map((job) => (
                <button
                  key={job.import_job_id}
                  onClick={() => setSelected(job.import_job_id)}
                  className={`w-full rounded-xl border p-3 text-left ${selected === job.import_job_id ? "border-emerald-400 bg-emerald-50" : "border-slate-200"}`}
                >
                  <div className="flex justify-between text-sm font-bold">
                    <span>{job.original_filename}</span>
                    <span>{job.status}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {job.valid_rows} valid · {job.invalid_rows} invalid ·{" "}
                    {new Date(job.created_at).toLocaleString()}
                  </p>
                </button>
              ))}
              {!jobs.data?.length && (
                <p className="text-sm text-slate-500">No imports yet.</p>
              )}
            </div>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-6">
            <div className="flex items-center justify-between">
              <h2 className="font-black">Row review</h2>
              {selected && invalid.length > 0 && (
                <span className="flex items-center gap-1 text-xs font-bold text-rose-700">
                  <AlertTriangle className="h-4 w-4" />
                  {invalid.length} need correction
                </span>
              )}
              {selected && invalid.length === 0 && rows.data?.length > 0 && (
                <button
                  onClick={() => commit.mutate()}
                  disabled={commit.isPending}
                  className="rounded-lg bg-slate-950 px-3 py-2 text-xs font-black text-white disabled:opacity-50"
                >
                  {commit.isPending ? "Queuing…" : "Confirm commit"}
                </button>
              )}
            </div>
            <div className="mt-4 space-y-2">
              {(rows.data || []).map((row) => (
                <div
                  key={row.import_row_id}
                  className="rounded-xl border border-slate-200 p-3"
                >
                  <div className="flex justify-between text-sm font-bold">
                    <span>Row {row.row_number}</span>
                    <span
                      className={
                        row.row_status === "VALID"
                          ? "text-emerald-700"
                          : "text-rose-700"
                      }
                    >
                      {row.row_status}
                    </span>
                  </div>
                  {row.error_items?.length > 0 && (
                    <p className="mt-1 text-xs text-rose-700">
                      {row.error_items.map((e) => e.message).join(" · ")}
                    </p>
                  )}
                </div>
              ))}
              {selected && !rows.data?.length && (
                <p className="text-sm text-slate-500">Loading row results…</p>
              )}
              {!selected && (
                <p className="text-sm text-slate-500">
                  Select an import to inspect row-level validation.
                </p>
              )}
            </div>
          </div>
        </section>
        {selected && staged.data?.length > 0 && (
          <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-black text-amber-950">
                  Onboarding handoff
                </h2>
                <p className="mt-1 text-sm text-amber-800">
                  These rows are staged safely. Account creation, farm
                  confirmation, and consent remain explicit.
                </p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-black text-amber-900">
                {staged.data.length} staged
              </span>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {staged.data.map((record) => (
                <article
                  key={record.staged_record_id}
                  className="rounded-2xl border border-amber-200 bg-white p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-black uppercase tracking-wide text-slate-500">
                      {record.record_type}
                    </span>
                    <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-black uppercase text-amber-900">
                      {String(record.status).replaceAll("_", " ")}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-700">
                    {record.status_reason}
                  </p>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </FpoFeatureGate>
  );
}
