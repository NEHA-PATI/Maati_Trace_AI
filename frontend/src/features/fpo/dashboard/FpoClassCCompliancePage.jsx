import { useCallback, useEffect, useState } from "react";
import { FileCheck2, Leaf, PackageOpen, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  getFpoComplianceDocuments,
  getFpoComplianceReadiness,
  getFpoDataPackSchemas,
  getFpoExportPacks,
  getFpoSustainabilityMetrics,
} from "../api/fpoPortalApi";

function Panel({ title, icon: Icon, children }) {
  const PanelIcon = Icon;
  return (
    <section className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50">
          <PanelIcon className="h-5 w-5 text-emerald-700" />
        </div>
        <h2 className="text-lg font-black leading-tight text-slate-950">{title}</h2>
      </div>
      <div className="mt-4 flex-1">{children}</div>
    </section>
  );
}

function PanelError({ children }) {
  return (
    <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
      {children}
    </p>
  );
}

function LoadingState() {
  return <p className="text-sm text-slate-500">Loading…</p>;
}

export default function FpoClassCCompliancePage() {
  const [documents, setDocuments] = useState([]);
  const [packs, setPacks] = useState([]);
  const [schemas, setSchemas] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [readiness, setReadiness] = useState(null);
  const [errors, setErrors] = useState({});
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const requests = [
      ["documents", getFpoComplianceDocuments, "Unable to load compliance documents."],
      ["readiness", getFpoComplianceReadiness, "Unable to load compliance readiness."],
      ["packs", getFpoExportPacks, "Unable to load export packs."],
      ["schemas", getFpoDataPackSchemas, "Unable to load data-pack schemas."],
      ["metrics", getFpoSustainabilityMetrics, "Unable to load sustainability metrics."],
    ];
    const results = await Promise.allSettled(
      requests.map(([, request]) => Promise.resolve().then(request)),
    );
    const nextErrors = {};

    results.forEach((result, index) => {
      const [key, , fallback] = requests[index];
      if (result.status === "rejected") {
        nextErrors[key] = result.reason?.message || fallback;
        return;
      }

      switch (key) {
        case "documents":
          setDocuments(result.value);
          break;
        case "readiness":
          setReadiness(result.value);
          break;
        case "packs":
          setPacks(result.value);
          break;
        case "schemas":
          setSchemas(result.value);
          break;
        case "metrics":
          setMetrics(result.value);
          break;
        default:
          break;
      }
    });

    setErrors(nextErrors);
    setLoaded(true);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-emerald-600">Class C · Governance</p>
          <h1 className="mt-1 text-2xl font-black text-slate-950">Compliance and data sharing</h1>
          <p className="mt-1 text-sm text-slate-500">Readiness, export packs and consent-bound data sharing with expiry-aware records.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading} className="rounded-xl">
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-5">
        <Panel title="Compliance readiness" icon={FileCheck2}>
          {loading && !loaded ? <LoadingState /> : null}
          {errors.readiness ? <PanelError>Compliance readiness is unavailable: {errors.readiness}</PanelError> : null}
          {readiness ? (
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-2xl font-black text-emerald-700">{readiness.complete ?? 0}</p>
                <p className="text-[10px] font-bold uppercase text-slate-400">Approved</p>
              </div>
              <div>
                <p className="text-2xl font-black text-amber-700">{readiness.under_review ?? 0}</p>
                <p className="text-[10px] font-bold uppercase text-slate-400">Review</p>
              </div>
              <div>
                <p className="text-2xl font-black text-rose-700">{readiness.expired ?? 0}</p>
                <p className="text-[10px] font-bold uppercase text-slate-400">Expired</p>
              </div>
            </div>
          ) : null}
          {loaded && !errors.readiness && !readiness ? <p className="text-sm text-slate-500">No readiness summary was returned.</p> : null}
        </Panel>

        <div className="grid gap-5 xl:grid-cols-3">
          <Panel title="Compliance documents" icon={FileCheck2}>
            {loading && !loaded ? <LoadingState /> : null}
            {errors.documents ? <PanelError>Compliance documents are unavailable: {errors.documents}</PanelError> : null}
            {documents.length ? (
              <div className="divide-y divide-slate-100">
                {documents.slice(0, 5).map((item) => (
                  <div key={item.compliance_document_id} className="flex justify-between py-2 text-sm">
                    <span>{item.document_type_code}</span>
                    <span className="text-xs font-bold text-slate-500">{item.review_status}</span>
                  </div>
                ))}
              </div>
            ) : null}
            {loaded && !errors.documents && !documents.length ? <p className="text-sm text-slate-500">No compliance documents are recorded.</p> : null}
          </Panel>

          <Panel title="Export packs" icon={PackageOpen}>
            {loading && !loaded ? <LoadingState /> : null}
            {errors.packs ? <PanelError>Export packs are unavailable: {errors.packs}</PanelError> : null}
            {packs.length ? (
              <div className="space-y-2">
                {packs.slice(0, 6).map((item) => (
                  <div key={item.export_pack_id} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                    <span className="font-semibold">{item.pack_code}</span>
                    <span className="text-xs font-bold text-slate-500">{item.status}</span>
                  </div>
                ))}
              </div>
            ) : null}
            {loaded && !errors.packs && !packs.length ? <p className="text-sm text-slate-500">No export packs have been requested.</p> : null}
          </Panel>

          <Panel title="Sustainability" icon={Leaf}>
            {loading && !loaded ? <LoadingState /> : null}
            {errors.metrics ? <PanelError>Sustainability metrics are unavailable: {errors.metrics}</PanelError> : null}
            {metrics.length ? (
              <div className="space-y-2">
                {metrics.slice(0, 6).map((item) => (
                  <div key={item.metric_id} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                    <span>{item.metric_code}</span>
                    <span className="font-bold">{item.metric_value} {item.unit_code}</span>
                  </div>
                ))}
              </div>
            ) : null}
            {loaded && !errors.metrics && !metrics.length ? <p className="text-sm text-slate-500">No published sustainability metrics are available.</p> : null}
          </Panel>
        </div>

        <Panel title="Published data-pack schemas" icon={FileCheck2}>
          {loading && !loaded ? <LoadingState /> : null}
          {errors.schemas ? <PanelError>Data-pack schemas are unavailable: {errors.schemas}</PanelError> : null}
          {schemas.length ? (
            <div className="grid gap-3 md:grid-cols-3">
              {schemas.map((schema) => (
                <div key={schema.data_pack_schema_id} className="rounded-xl border border-slate-100 p-4">
                  <p className="font-bold text-slate-900">{schema.name}</p>
                  <p className="mt-1 text-xs text-slate-500">{schema.schema_key} v{schema.version} · {schema.purpose_code}</p>
                  <p className="mt-2 text-xs text-slate-400">Only grant-authorized fields may be generated.</p>
                </div>
              ))}
            </div>
          ) : null}
          {loaded && !errors.schemas && !schemas.length ? <p className="text-sm text-slate-500">No admin-published data-pack schemas are available.</p> : null}
        </Panel>
      </div>
    </div>
  );
}
