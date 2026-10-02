import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, FileUp, ShieldCheck, Download } from "lucide-react";
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

function rowPayload(row) {
  if (!row?.normalized_payload) return {};
  return typeof row.normalized_payload === "string"
    ? JSON.parse(row.normalized_payload)
    : row.normalized_payload;
}

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function BoundaryPreview({ geometry }) {
  const ring = geometry?.type === "Polygon"
    ? geometry.coordinates?.[0]
    : geometry?.type === "MultiPolygon" ? geometry.coordinates?.[0]?.[0] : null;
  const points = Array.isArray(ring) ? ring.filter((point) => Array.isArray(point) && point.length > 1) : [];
  if (points.length < 3) return <div className="flex h-44 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 text-center text-xs text-slate-400">A valid farm boundary preview will appear here.</div>;
  const xs = points.map(([x]) => Number(x)); const ys = points.map(([, y]) => Number(y));
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const coords = points.map(([x, y]) => `${12 + ((Number(x) - minX) / (maxX - minX || 1)) * 176},${188 - ((Number(y) - minY) / (maxY - minY || 1)) * 176}`).join(" ");
  return <div className="relative h-44 overflow-hidden rounded-2xl border border-emerald-100 bg-[linear-gradient(#e7f5ed_1px,transparent_1px),linear-gradient(90deg,#e7f5ed_1px,transparent_1px)] bg-[size:22px_22px]"><svg viewBox="0 0 200 200" className="h-full w-full"><polygon points={coords} fill="#34d399" fillOpacity=".3" stroke="#047857" strokeWidth="2.5" /></svg><span className="absolute bottom-2 left-2 rounded-full bg-white/90 px-2 py-1 text-[10px] font-bold text-emerald-800">GeoJSON boundary preview</span></div>;
}

export default function FpoImportsPage() {
  const [type, setType] = useState("FARMERS");
  const [file, setFile] = useState(null);
  const [selected, setSelected] = useState(null);
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState("ALL");
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
  const visibleRows = useMemo(
    () => (rows.data || []).filter((row) => filter === "ALL" || row.row_status === filter),
    [filter, rows.data],
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

  function downloadReport() {
    const header = ["row_number", "status", "farmer_name", "farm_name", "crop_name", "crop_stage", "planting_date", "errors"];
    const body = (rows.data || []).map((row) => {
      const payload = rowPayload(row);
      return [row.row_number, row.row_status, payload.farmer_name, payload.farm_name, payload.crop_name, payload.crop_stage, payload.planting_date, (row.error_items || []).map((error) => error.message).join(" | ")].map(csvCell).join(",");
    });
    const url = URL.createObjectURL(new Blob([[header.map(csvCell).join(","), ...body].join("\n")], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "maatitrace-import-validation-report.csv"; link.click(); URL.revokeObjectURL(url);
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
      <div className="space-y-6 pb-10">
        <header className="relative overflow-hidden rounded-[2rem] bg-slate-950 p-7 text-white shadow-xl sm:p-9">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-700">
            Class B · Growth operations
          </p>
          <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
            Bulk onboarding, built for trust
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Upload a versioned CSV or XLSX, validate every farm boundary and crop
            detail, then stage records for consent. No farmer, FPO, farm or
            external reference is entered by the operator.
          </p>
          <div className="mt-5 flex flex-wrap gap-2 text-xs font-bold"><span className="rounded-full bg-white/10 px-3 py-1.5">Up to 5,000 rows</span><span className="rounded-full bg-white/10 px-3 py-1.5">Dry run required</span><span className="rounded-full bg-emerald-400/20 px-3 py-1.5 text-emerald-200">Consent protected</span></div>
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
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><p className="text-xs font-black uppercase tracking-[0.16em] text-slate-400">Step 2 · review</p><h2 className="mt-1 font-black">Row review</h2></div>
              {selected && <button type="button" onClick={downloadReport} className="inline-flex items-center gap-1 rounded-xl border border-slate-200 px-3 py-2 text-xs font-black text-slate-700"><Download className="h-4 w-4" />Export validation report</button>}
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
            {selected && <div className="mt-4 grid grid-cols-3 gap-2"><div className="rounded-xl bg-slate-50 p-3"><p className="text-xl font-black">{rows.data?.length || 0}</p><p className="text-[10px] font-bold uppercase text-slate-400">Total</p></div><div className="rounded-xl bg-emerald-50 p-3"><p className="text-xl font-black text-emerald-700">{(rows.data?.length || 0) - invalid.length}</p><p className="text-[10px] font-bold uppercase text-emerald-700/60">Valid</p></div><div className="rounded-xl bg-rose-50 p-3"><p className="text-xl font-black text-rose-700">{invalid.length}</p><p className="text-[10px] font-bold uppercase text-rose-700/60">Errors</p></div></div>}
            {selected && <div className="mt-4 flex gap-2">{["ALL", "VALID", "INVALID"].map((value) => <button type="button" key={value} onClick={() => setFilter(value)} className={`rounded-full px-3 py-1.5 text-xs font-black ${filter === value ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-500"}`}>{value === "ALL" ? "All rows" : value === "VALID" ? "Valid" : "Needs correction"}</button>)}</div>}
            <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_.8fr]"><div className="space-y-2">
              {visibleRows.map((row) => (
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
            </div><BoundaryPreview geometry={selected ? rowPayload(visibleRows[0] || rows.data?.[0]).polygon_geojson : null} /></div>
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
