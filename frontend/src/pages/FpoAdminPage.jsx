import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  FileCheck2,
  RefreshCw,
  XCircle,
  ShieldCheck,
  Plus,
  Send,
  Archive,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import {
  assignFpoClass,
  createFpoFeatureOverride,
  getFpoFeatureCatalogue,
  getFpoFeatureOverrides,
  getFpoVerificationQueue,
  getFpoAdminDocuments,
  getFpoAdminDocumentContent,
  validateFpoDocument,
  getFpoAdminChecklist,
  updateFpoAdminChecklist,
  reviewFpoVerification,
  runFpoReconciliation,
  getFpoAdminAdvisoryTemplates,
  createFpoAdminAdvisoryTemplate,
  reviewFpoAdminAdvisoryTemplate,
  getFpoClassBReleaseReadiness,
  publishFpoClassBPlan,
  getFpoClassCReleaseReadiness,
  publishFpoClassCPlan,
} from "@/lib/api/fpo";
import { fpoAccessApi } from "@/features/fpo-access/api/fpoAccessApi";

const TABS = ["verification", "access", "configuration", "governance"];
const FILTERS = [
  ["", "All submissions"],
  ["SUBMITTED", "Submitted"],
  ["UNDER_REVIEW", "Under review"],
  ["CHANGES_REQUIRED", "Changes required"],
  ["APPROVED", "Approved"],
  ["REJECTED", "Rejected"],
];

function readableStatus(value) {
  return String(value || "PROFILE_INCOMPLETE").replaceAll("_", " ");
}

export default function FpoAdminPage() {
  const [tab, setTab] = useState("verification");
  const [filter, setFilter] = useState("");
  const [items, setItems] = useState([]);
  const [accessItems, setAccessItems] = useState([]);
  const [accessLoading, setAccessLoading] = useState(false);
  const [accessBusyId, setAccessBusyId] = useState("");
  const [selected, setSelected] = useState(null);
  const [checklist, setChecklist] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [openingDocumentId, setOpeningDocumentId] = useState("");
  const [validatingDocumentId, setValidatingDocumentId] = useState("");
  const [note, setNote] = useState("");
  const [classCode, setClassCode] = useState("A");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reconciliation, setReconciliation] = useState(null);
  const [featureCatalogue, setFeatureCatalogue] = useState([]);
  const [overrides, setOverrides] = useState([]);
  const [overrideTarget, setOverrideTarget] = useState(null);
  const [overrideFeature, setOverrideFeature] = useState("");
  const [overrideEnabled, setOverrideEnabled] = useState(true);
  const [overrideReason, setOverrideReason] = useState("");
  const [templates, setTemplates] = useState([]);
  const [readiness, setReadiness] = useState(null);
  const [classCReadiness, setClassCReadiness] = useState(null);
  const [templateForm, setTemplateForm] = useState({
    template_code: "",
    name: "",
    advisory_type: "GENERAL",
    language_code: "en",
    title_template: "",
    body_template: "",
  });

  async function loadFeatureConfiguration() {
    try {
      setFeatureCatalogue(await getFpoFeatureCatalogue());
    } catch (requestError) {
      setError(
        requestError?.message || "Unable to load the FPO feature catalogue.",
      );
    }
  }

  async function loadQueue() {
    setLoading(true);
    setError("");
    try {
      setItems(await getFpoVerificationQueue(filter));
    } catch (requestError) {
      setError(
        requestError?.message || "Unable to load FPO verification submissions.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadAccessRequests() {
    setAccessLoading(true);
    try {
      const result = await fpoAccessApi.listForAdmin({});
      setAccessItems(result.items || []);
    } catch (requestError) {
      setError(requestError?.message || "Unable to load FPO access requests.");
    } finally {
      setAccessLoading(false);
    }
  }

  useEffect(() => {
    loadQueue();
  }, [filter]);

  useEffect(() => {
    if (tab === "configuration") loadFeatureConfiguration();
    if (tab === "access") loadAccessRequests();
  }, [tab]);

  async function decideAccess(item, status) {
    setAccessBusyId(item.request_id);
    setError("");
    try {
      await fpoAccessApi.reviewForAdmin(item.request_id, {
        status,
        review_note:
          status === "rejected"
            ? "Request rejected by administrator."
            : "Approved for secure FPO invitation.",
      });
      await loadAccessRequests();
    } catch (requestError) {
      setError(
        requestError?.message || "The FPO access decision could not be saved.",
      );
    } finally {
      setAccessBusyId("");
    }
  }

  async function approveAndInvite(item) {
    setAccessBusyId(item.request_id);
    setError("");
    setNotice("");
    try {
      if (item.status === "pending") {
        await fpoAccessApi.reviewForAdmin(item.request_id, {
          status: "approved",
          review_note: "Approved for secure FPO invitation.",
        });
      }
      await fpoAccessApi.createInvitation({
        email: item.contact_email,
        role: "fpo",
        metadata: {
          organisation_name: item.organisation_name,
          contact_person_name: item.contact_person_name,
          access_request_id: item.request_id,
        },
      });
      await fpoAccessApi.reviewForAdmin(item.request_id, {
        status: "closed",
        review_note: "FPO invitation queued successfully.",
      });
      setNotice(
        `Invitation queued for ${item.contact_email}. The user must accept the email invitation to create the FPO account.`,
      );
      await loadAccessRequests();
    } catch (requestError) {
      setError(
        requestError?.message || "The FPO invitation could not be queued.",
      );
      await loadAccessRequests();
    } finally {
      setAccessBusyId("");
    }
  }

  useEffect(() => {
    if (tab !== "governance") return;
    Promise.all([
      getFpoAdminAdvisoryTemplates(),
      getFpoClassBReleaseReadiness(),
      getFpoClassCReleaseReadiness(),
    ])
      .then(([templateRows, release, classCRelease]) => {
        setTemplates(templateRows);
        setReadiness(release);
        setClassCReadiness(classCRelease);
      })
      .catch((requestError) =>
        setError(requestError?.message || "Unable to load release governance."),
      );
  }, [tab]);

  useEffect(() => {
    if (!selected) return;
    getFpoFeatureOverrides(selected.fpo_id)
      .then(setOverrides)
      .catch((requestError) =>
        setError(requestError?.message || "Unable to load feature overrides."),
      );
    getFpoAdminChecklist(selected.fpo_id)
      .then(setChecklist)
      .catch((requestError) =>
        setError(
          requestError?.message || "Unable to load verification checklist.",
        ),
      );
    getFpoAdminDocuments(selected.fpo_id)
      .then(setDocuments)
      .catch((requestError) =>
        setError(
          requestError?.message || "Unable to load verification documents.",
        ),
      );
  }, [selected]);

  async function updateChecklist(item, result) {
    setSaving(true);
    setError("");
    try {
      const updated = await updateFpoAdminChecklist(
        item.checklist_result_id,
        result,
        `Reviewed in FPO management: ${result}`,
      );
      setChecklist((current) =>
        current.map((row) =>
          row.checklist_result_id === item.checklist_result_id ? updated : row,
        ),
      );
    } catch (requestError) {
      setError(
        requestError?.message || "The checklist item could not be updated.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function viewDocument(document) {
    setOpeningDocumentId(document.document_id);
    setError("");
    try {
      const blob = await getFpoAdminDocumentContent(document.document_id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (requestError) {
      setError(requestError?.message || "The document could not be opened.");
    } finally {
      setOpeningDocumentId("");
    }
  }

  async function validateDocument(document, validationStatus) {
    setValidatingDocumentId(document.document_id);
    setError("");
    try {
      const updated = await validateFpoDocument(
        document.document_id,
        validationStatus,
        validationStatus === "VALID"
          ? "Document reviewed and accepted."
          : "Document reviewed and rejected.",
      );
      setDocuments((current) =>
        current.map((item) =>
          item.document_id === document.document_id
            ? { ...item, ...updated }
            : item,
        ),
      );
    } catch (requestError) {
      setError(
        requestError?.message || "The document validation could not be saved.",
      );
    } finally {
      setValidatingDocumentId("");
    }
  }

  useEffect(() => {
    if (!overrideTarget || tab !== "configuration") return;
    getFpoFeatureOverrides(overrideTarget.fpo_id)
      .then(setOverrides)
      .catch((requestError) =>
        setError(requestError?.message || "Unable to load feature overrides."),
      );
  }, [overrideTarget, tab]);

  const counts = useMemo(
    () =>
      items.reduce((result, item) => {
        const key = item.verification_status || "PROFILE_INCOMPLETE";
        result[key] = (result[key] || 0) + 1;
        return result;
      }, {}),
    [items],
  );

  async function decide(status) {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      await reviewFpoVerification(selected.fpo_id, status, note);
      setSelected(null);
      setNote("");
      await loadQueue();
    } catch (requestError) {
      setError(
        requestError?.message ||
          "The verification decision could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function assignClass() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      await assignFpoClass(selected.fpo_id, classCode);
      setSelected((current) =>
        current ? { ...current, class_code: classCode } : current,
      );
      await loadQueue();
    } catch (requestError) {
      setError(requestError?.message || "The FPO class could not be assigned.");
    } finally {
      setSaving(false);
    }
  }

  async function reconcile() {
    setSaving(true);
    setError("");
    try {
      setReconciliation(await runFpoReconciliation());
    } catch (requestError) {
      setError(
        requestError?.message ||
          "The FPO reconciliation could not be completed.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function saveOverride() {
    if (!overrideTarget || !overrideFeature || overrideReason.trim().length < 3)
      return;
    setSaving(true);
    setError("");
    try {
      await createFpoFeatureOverride(overrideTarget.fpo_id, {
        feature_key: overrideFeature,
        enabled: overrideEnabled,
        reason: overrideReason.trim(),
      });
      setOverrides(await getFpoFeatureOverrides(overrideTarget.fpo_id));
      setOverrideReason("");
    } catch (requestError) {
      setError(
        requestError?.message || "The feature override could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function saveTemplate(event) {
    event.preventDefault();
    setSaving(true);
    try {
      const created = await createFpoAdminAdvisoryTemplate(templateForm);
      setTemplates((current) => [created, ...current]);
      setTemplateForm({
        template_code: "",
        name: "",
        advisory_type: "GENERAL",
        language_code: "en",
        title_template: "",
        body_template: "",
      });
    } catch (requestError) {
      setError(
        requestError?.message || "The advisory template could not be created.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function reviewTemplate(templateId, decision) {
    setSaving(true);
    try {
      const updated = await reviewFpoAdminAdvisoryTemplate(
        templateId,
        decision,
      );
      setTemplates((current) =>
        current.map((item) =>
          item.template_id === templateId ? updated : item,
        ),
      );
    } catch (requestError) {
      setError(
        requestError?.message || "The template decision could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function publishClassB() {
    setSaving(true);
    try {
      const published = await publishFpoClassBPlan(
        "Approved after admin release-readiness review",
      );
      setReadiness((current) => ({
        ...current,
        plan: published,
        ready: false,
      }));
    } catch (requestError) {
      setError(
        requestError?.message ||
          "Class B cannot be published until all gates pass.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function publishClassC() {
    setSaving(true);
    try {
      const published = await publishFpoClassCPlan(
        "Approved after Class C release-readiness review",
      );
      setClassCReadiness((current) => ({
        ...current,
        plan: published,
        ready: false,
      }));
    } catch (requestError) {
      setError(
        requestError?.message ||
          "Class C cannot be published until all gates pass.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-emerald-600">
            Admin / FPO
          </p>
          <h1 className="mt-1 text-2xl font-black text-slate-950">
            FPO management
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Review onboarding, verification, and organization controls from one
            workspace.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={loadQueue}
          disabled={loading}
          className="rounded-xl"
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
          />{" "}
          Refresh
        </Button>
      </div>

      <div className="flex w-full gap-3 overflow-x-auto rounded-2xl border border-slate-200 bg-slate-50 p-1.5" role="tablist" aria-label="FPO administration sections">
        {TABS.map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setTab(value)}
            role="tab"
            aria-selected={tab === value}
            className={`min-w-[140px] flex-1 rounded-xl px-5 py-2.5 text-sm font-bold capitalize transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${tab === value ? "bg-emerald-700 text-white shadow-sm" : "text-slate-600 hover:bg-white hover:text-emerald-700"}`}
          >
            {value}
          </button>
        ))}
      </div>

      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
        >
          {error}
        </div>
      ) : null}
      {notice ? (
        <div
          role="status"
          className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"
        >
          {notice}
        </div>
      ) : null}

      {tab === "access" ? (
        <section className="space-y-4">
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <h2 className="font-black text-amber-950">FPO access requests</h2>
            <p className="mt-1 text-sm leading-6 text-amber-900">
              These requests ask for a new FPO account and invitation. They are
              intentionally separate from organization profile verification
              below.
            </p>
          </div>
          {accessLoading ? (
            <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
              Loading access requests…
            </p>
          ) : null}
          {!accessLoading && accessItems.length === 0 ? (
            <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
              No pending or approved access requests.
            </p>
          ) : null}
          <div className="space-y-3">
            {accessItems.map((item) => {
              const busy = accessBusyId === item.request_id;
              return (
                <article
                  key={item.request_id}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-bold text-slate-950">
                          {item.organisation_name}
                        </h3>
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold uppercase text-slate-600">
                          {item.status}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">
                        {item.contact_person_name} · {item.contact_email} ·{" "}
                        {item.contact_phone}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">
                        {[item.district_name, item.state_name]
                          .filter(Boolean)
                          .join(", ")}
                      </p>
                      {item.registration_number ? (
                        <p className="mt-1 text-xs text-slate-500">
                          Registration: {item.registration_number}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {item.status === "pending" ? (
                        <Button
                          variant="outline"
                          disabled={busy}
                          onClick={() => decideAccess(item, "rejected")}
                          className="rounded-lg text-rose-700"
                        >
                          Reject
                        </Button>
                      ) : null}
                      {item.status === "pending" ||
                      item.status === "approved" ? (
                        <Button
                          disabled={busy}
                          onClick={() => approveAndInvite(item)}
                          className="rounded-lg bg-emerald-700 hover:bg-emerald-800"
                        >
                          {busy
                            ? "Working…"
                            : item.status === "approved"
                              ? "Retry invitation"
                              : "Approve and invite"}
                        </Button>
                      ) : (
                        <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold uppercase text-slate-500">
                          {item.status === "closed"
                            ? "Invitation sent"
                            : "No action"}
                        </span>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ) : tab === "configuration" ? (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-5">
            <div>
              <p className="font-bold text-emerald-950">
                Data integrity reconciliation
              </p>
              <p className="mt-1 text-sm text-emerald-800">
                Repair safe farmer-to-FPO projection drift and report
                provisioning gaps.
              </p>
            </div>
            <Button
              onClick={reconcile}
              disabled={saving}
              className="rounded-xl bg-emerald-700 hover:bg-emerald-800"
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${saving ? "animate-spin" : ""}`}
              />{" "}
              Run reconciliation
            </Button>
          </div>
          {reconciliation ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
              Completed: repaired {reconciliation.repaired_farmer_projections},
              cleared {reconciliation.cleared_stale_projections}, orphaned
              organizations {reconciliation.orphaned_organizations}.
            </div>
          ) : null}
          <div className="grid gap-4 md:grid-cols-3">
            {[
              [
                "Verification policy",
                "Profile completion is required before submission. Approval enables discovery.",
              ],
              [
                "Organization model",
                "One active owner account per FPO. Staff accounts are disabled for this release.",
              ],
              [
                "Provisioning",
                "New FPO accounts are provisioned through the auth outbox worker with retry support.",
              ],
            ].map(([title, description]) => (
              <div
                key={title}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <p className="font-bold text-slate-900">{title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {description}
                </p>
                <span className="mt-4 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                  Active
                </span>
              </div>
            ))}
          </div>
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-black text-slate-950">Feature catalogue</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Published Class A/B/C capabilities available for controlled
                  assignment.
                </p>
              </div>
              <span className="text-xs font-bold text-slate-400">
                {featureCatalogue.length} features
              </span>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {featureCatalogue.map((feature) => (
                <div
                  key={`${feature.feature_key}-${feature.class_code || "catalogue"}`}
                  className="rounded-xl border border-slate-100 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-slate-900">
                        {feature.display_name || feature.feature_key}
                      </p>
                      <p className="mt-1 text-xs font-mono text-slate-400">
                        {feature.feature_key}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-1 text-[10px] font-black uppercase ${feature.is_active === false ? "bg-slate-100 text-slate-500" : "bg-emerald-50 text-emerald-700"}`}
                    >
                      {feature.class_code
                        ? `Class ${feature.class_code}`
                        : feature.category || "Active"}
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">
                    {feature.description}
                  </p>
                  {feature.enabled !== undefined ? (
                    <p className="mt-2 text-xs font-bold text-slate-500">
                      Default: {feature.enabled ? "Enabled" : "Disabled"}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-black text-slate-950">
              Per-FPO feature overrides
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Apply a time-bounded, audited exception to the published class
              configuration.
            </p>
            <select
              value={overrideTarget?.fpo_id || ""}
              onChange={(event) =>
                setOverrideTarget(
                  items.find((item) => item.fpo_id === event.target.value) ||
                    null,
                )
              }
              className="mt-4 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">Select an FPO</option>
              {items.map((item) => (
                <option key={item.fpo_id} value={item.fpo_id}>
                  {item.fpo_name || item.public_fpo_id || item.fpo_id}
                </option>
              ))}
            </select>
            {overrideTarget ? (
              <>
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  <select
                    value={overrideFeature}
                    onChange={(event) => setOverrideFeature(event.target.value)}
                    className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
                  >
                    <option value="">Select feature</option>
                    {featureCatalogue
                      .filter(
                        (feature) =>
                          feature.is_active !== false && feature.feature_key,
                      )
                      .map((feature) => (
                        <option
                          key={feature.feature_key}
                          value={feature.feature_key}
                        >
                          {feature.display_name || feature.feature_key}
                        </option>
                      ))}
                  </select>
                  <select
                    value={overrideEnabled ? "true" : "false"}
                    onChange={(event) =>
                      setOverrideEnabled(event.target.value === "true")
                    }
                    className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
                  >
                    <option value="true">Enable</option>
                    <option value="false">Disable</option>
                  </select>
                </div>
                <input
                  value={overrideReason}
                  onChange={(event) => setOverrideReason(event.target.value)}
                  placeholder="Reason / ticket reference"
                  className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                />
                <Button
                  className="mt-2 rounded-xl bg-slate-900"
                  onClick={saveOverride}
                  disabled={
                    saving ||
                    !overrideFeature ||
                    overrideReason.trim().length < 3
                  }
                >
                  Save override
                </Button>
                <div className="mt-4 space-y-2">
                  {overrides.length ? (
                    overrides.map((override) => (
                      <div
                        key={override.override_id}
                        className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs"
                      >
                        <span className="font-bold text-slate-700">
                          {override.feature_key}
                        </span>
                        <span
                          className={
                            override.enabled
                              ? "text-emerald-700"
                              : "text-rose-700"
                          }
                        >
                          {override.enabled ? "Enabled" : "Disabled"} ·{" "}
                          {override.reason}
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-400">
                      No overrides for this FPO.
                    </p>
                  )}
                </div>
              </>
            ) : (
              <p className="mt-4 text-sm text-slate-500">
                Select an FPO to manage its feature overrides.
              </p>
            )}
          </section>
        </div>
      ) : tab === "governance" ? (
        <div className="space-y-4">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-black text-slate-950">
                  Release governance
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Every release remains auditable, versioned and explicitly
                  controlled.
                </p>
              </div>
              <ShieldCheck className="h-6 w-6 text-emerald-600" />
            </div>
            {readiness ? (
              <>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Plan
                    </p>
                    <p className="mt-1 font-black text-slate-900">
                      Class {readiness.plan?.class_code} v
                      {readiness.plan?.version}
                    </p>
                    <p className="text-xs text-slate-500">
                      {readiness.plan?.status}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Gate result
                    </p>
                    <p
                      className={`mt-1 font-black ${readiness.ready ? "text-emerald-700" : "text-amber-700"}`}
                    >
                      {readiness.ready ? "Ready" : "Blocked"}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Controls
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Publishing is manual and audited.
                    </p>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  {readiness.checks?.map((check) => (
                    <div
                      key={check.check_key}
                      className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-sm"
                    >
                      <span className="font-semibold text-slate-700">
                        {check.check_key.replaceAll("_", " ")}
                      </span>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-black ${check.status === "PASS" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}
                      >
                        {check.status}
                      </span>
                    </div>
                  ))}
                </div>
                <Button
                  onClick={publishClassB}
                  disabled={
                    saving ||
                    !readiness.ready ||
                    readiness.plan?.status !== "DRAFT"
                  }
                  className="mt-4 rounded-xl bg-slate-900"
                >
                  <Send className="mr-2 h-4 w-4" /> Publish Class B plan
                </Button>
              </>
            ) : (
              <p className="mt-4 text-sm text-slate-500">
                Loading readiness checks…
              </p>
            )}
            {classCReadiness ? (
              <div className="mt-5 rounded-xl border border-violet-100 bg-violet-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-black text-violet-950">
                      Class C v{classCReadiness.plan?.version} ·{" "}
                      {classCReadiness.plan?.status}
                    </p>
                    <p className="mt-1 text-sm text-violet-800">
                      {classCReadiness.ready
                        ? "All structural release checks pass."
                        : "Class C is blocked until every release check passes."}
                    </p>
                  </div>
                  <Button
                    onClick={publishClassC}
                    disabled={
                      saving ||
                      !classCReadiness.ready ||
                      classCReadiness.plan?.status !== "DRAFT"
                    }
                    className="rounded-xl bg-violet-700 hover:bg-violet-800"
                  >
                    <Send className="mr-2 h-4 w-4" /> Publish Class C
                  </Button>
                </div>
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  {classCReadiness.checks?.map((check) => (
                    <div
                      key={check.check_key}
                      className="rounded-lg bg-white/70 px-3 py-2 text-xs"
                    >
                      <span className="font-semibold text-violet-900">
                        {check.check_key.replaceAll("_", " ")}
                      </span>
                      <span
                        className={`ml-2 font-black ${check.status === "PASS" ? "text-emerald-700" : "text-rose-700"}`}
                      >
                        {check.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-black text-slate-950">
                  Advisory template catalogue
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Admin-owned templates require safety review before
                  publication.
                </p>
              </div>
              <span className="text-xs font-bold text-slate-400">
                {templates.length} templates
              </span>
            </div>
            <form
              onSubmit={saveTemplate}
              className="mt-4 grid gap-2 rounded-xl bg-slate-50 p-4 md:grid-cols-2"
            >
              <input
                required
                value={templateForm.template_code}
                onChange={(event) =>
                  setTemplateForm({
                    ...templateForm,
                    template_code: event.target.value,
                  })
                }
                placeholder="Template code"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <input
                required
                value={templateForm.name}
                onChange={(event) =>
                  setTemplateForm({ ...templateForm, name: event.target.value })
                }
                placeholder="Template name"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <select
                value={templateForm.advisory_type}
                onChange={(event) =>
                  setTemplateForm({
                    ...templateForm,
                    advisory_type: event.target.value,
                  })
                }
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option>GENERAL</option>
                <option>NUTRIENT</option>
                <option>CROP_PROTECTION</option>
                <option>WEATHER</option>
                <option>IRRIGATION</option>
                <option>STAGE_ACTIVITY</option>
              </select>
              <input
                required
                value={templateForm.language_code}
                onChange={(event) =>
                  setTemplateForm({
                    ...templateForm,
                    language_code: event.target.value,
                  })
                }
                placeholder="Language code"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <input
                required
                value={templateForm.title_template}
                onChange={(event) =>
                  setTemplateForm({
                    ...templateForm,
                    title_template: event.target.value,
                  })
                }
                placeholder="Title template"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <textarea
                required
                value={templateForm.body_template}
                onChange={(event) =>
                  setTemplateForm({
                    ...templateForm,
                    body_template: event.target.value,
                  })
                }
                placeholder="Body template"
                rows={3}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm md:col-span-2"
              />
              <Button
                type="submit"
                disabled={saving}
                className="w-fit rounded-lg bg-emerald-700"
              >
                <Plus className="mr-2 h-4 w-4" /> Create draft
              </Button>
            </form>
            <div className="mt-4 divide-y divide-slate-100">
              {templates.map((template) => (
                <div
                  key={template.template_id}
                  className="flex flex-wrap items-center justify-between gap-3 py-3"
                >
                  <div>
                    <p className="font-bold text-slate-900">{template.name}</p>
                    <p className="text-xs text-slate-500">
                      {template.template_code} · {template.language_code} ·{" "}
                      {template.status} · safety {template.safety_review_status}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {template.status === "DRAFT" ? (
                      <Button
                        variant="outline"
                        disabled={saving}
                        onClick={() =>
                          reviewTemplate(template.template_id, "APPROVE")
                        }
                        className="rounded-lg text-emerald-700"
                      >
                        <CheckCircle2 className="mr-1 h-4 w-4" /> Approve
                      </Button>
                    ) : null}
                    {template.status !== "RETIRED" ? (
                      <Button
                        variant="outline"
                        disabled={saving}
                        onClick={() =>
                          reviewTemplate(template.template_id, "RETIRE")
                        }
                        className="rounded-lg text-slate-600"
                      >
                        <Archive className="mr-1 h-4 w-4" /> Retire
                      </Button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              ["SUBMITTED", "Awaiting review"],
              ["UNDER_REVIEW", "In review"],
              ["APPROVED", "Approved"],
            ].map(([key, label]) => (
              <div
                key={key}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {label}
                </p>
                <p className="mt-2 text-2xl font-black text-slate-950">
                  {counts[key] || 0}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap gap-2 border-b border-slate-100 p-4">
              {FILTERS.map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setFilter(value)}
                  className={`rounded-full px-3 py-1.5 text-xs font-bold ${filter === value ? "bg-emerald-700 text-white" : "bg-slate-100 text-slate-600"}`}
                >
                  {label}
                </button>
              ))}
            </div>
            {loading ? (
              <p className="p-6 text-sm text-slate-500">
                Loading FPO submissions…
              </p>
            ) : items.length === 0 ? (
              <p className="p-8 text-center text-sm text-slate-500">
                No FPO submissions in this queue.
              </p>
            ) : (
              <div className="divide-y divide-slate-100">
                {items.map((item) => (
                  <div
                    key={item.fpo_id}
                    className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between"
                  >
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <p className="font-bold text-slate-900">
                          {item.fpo_name || "FPO profile pending"}
                        </p>
                        <VerificationStamp
                          label={readableStatus(item.verification_status)}
                          type={
                            item.verification_status === "APPROVED"
                              ? "success"
                              : "pending"
                          }
                          compact
                        />
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.public_fpo_id || "Public ID pending"} ·{" "}
                        {item.district_name || "District pending"},{" "}
                        {item.state_name || "State pending"}
                      </p>
                      <p className="mt-2 text-sm text-slate-600">
                        Representative: {item.contact_person_name || "Pending"}{" "}
                        · {item.contact_email || "No email"}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      className="rounded-xl"
                      onClick={() => {
                        setSelected(item);
                        setClassCode(item.class_code || "A");
                        setNote(item.reviewer_note || "");
                      }}
                    >
                      <FileCheck2 className="mr-2 h-4 w-4" /> Review
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {selected ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
            <p className="text-xs font-bold uppercase tracking-wider text-emerald-600">
              Verification decision
            </p>
            <h2 className="mt-1 text-xl font-black text-slate-950">
              {selected.fpo_name || "FPO profile"}
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              {selected.registration_type || "Registration type pending"} ·{" "}
              {selected.registration_number || "Registration number pending"}
            </p>
            <section className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-sm font-black text-slate-900">FPO fields</h3>
              <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                <p>
                  <b>Name:</b> {selected.fpo_name || "—"}
                </p>
                <p>
                  <b>Representative:</b> {selected.contact_person_name || "—"}
                </p>
                <p>
                  <b>Email:</b> {selected.contact_email || "—"}
                </p>
                <p>
                  <b>Phone:</b> {selected.contact_phone || "—"}
                </p>
                <p>
                  <b>Registration:</b> {selected.registration_number || "—"}
                </p>
                <p>
                  <b>Location:</b>{" "}
                  {[selected.district_name, selected.state_name]
                    .filter(Boolean)
                    .join(", ") || "—"}
                </p>
              </div>
            </section>
            <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-black text-slate-900">
                    Uploaded documents
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Open each document and validate it before approval.
                  </p>
                </div>
                <span className="text-xs font-bold text-slate-500">
                  {documents.length} files
                </span>
              </div>
              <div className="mt-3 space-y-2">
                {documents.length ? (
                  documents.map((document) => (
                    <div
                      key={document.document_id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-100 p-3"
                    >
                      <div>
                        <p className="text-sm font-bold text-slate-800">
                          {document.original_filename}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {readableStatus(document.document_type)} · scan{" "}
                          {readableStatus(document.scan_status)} · validation{" "}
                          {readableStatus(document.validation_status)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => viewDocument(document)}
                          disabled={openingDocumentId === document.document_id}
                        >
                          {openingDocumentId === document.document_id
                            ? "Opening…"
                            : "View"}
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-rose-700">
                    No documents are attached to this submission.
                  </p>
                )}
              </div>
            </section>
            <section className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-black text-slate-900">
                    Verification checklist
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Mark every item Pass or Not applicable before approval.
                  </p>
                </div>
                <span className="text-xs font-bold text-slate-500">
                  {
                    checklist.filter((item) =>
                      ["PASS", "NOT_APPLICABLE"].includes(item.result),
                    ).length
                  }
                  /{checklist.length}
                </span>
              </div>
              <div className="mt-3 space-y-2">
                {checklist.length ? (
                  checklist.map((item) => (
                    <div
                      key={item.checklist_result_id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white bg-white p-3"
                    >
                      <div>
                        <p className="text-sm font-bold text-slate-800">
                          {readableStatus(item.checklist_key)}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          Current: {readableStatus(item.result)}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant={
                            item.result === "PASS" ? "default" : "outline"
                          }
                          onClick={() => updateChecklist(item, "PASS")}
                          disabled={saving}
                        >
                          Pass
                        </Button>
                        <Button
                          size="sm"
                          variant={
                            item.result === "NOT_APPLICABLE"
                              ? "default"
                              : "outline"
                          }
                          onClick={() =>
                            updateChecklist(item, "NOT_APPLICABLE")
                          }
                          disabled={saving}
                        >
                          N/A
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-rose-700">
                    No checklist was created for this submission.
                  </p>
                )}
              </div>
            </section>
            <label
              className="mt-5 block text-sm font-bold text-slate-700"
              htmlFor="review-note"
            >
              Reviewer note
            </label>
            <textarea
              id="review-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={4}
              placeholder="Required for approval. Add a reason or review note…"
              className="mt-2 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-emerald-600"
            />
            <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3">
              <label
                htmlFor="fpo-class"
                className="block text-xs font-bold uppercase tracking-wider text-slate-500"
              >
                FPO class
              </label>
              <div className="mt-2 flex gap-2">
                <select
                  id="fpo-class"
                  value={classCode}
                  onChange={(event) => setClassCode(event.target.value)}
                  className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
                >
                  <option value="A">Class A · Foundation</option>
                  <option value="B">Class B · Growth</option>
                  <option value="C">Class C · Commercial</option>
                </select>
                <Button
                  variant="outline"
                  onClick={assignClass}
                  disabled={saving}
                >
                  Assign class
                </Button>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setSelected(null)}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                variant="outline"
                onClick={() => decide("CHANGES_REQUIRED")}
                disabled={saving}
              >
                <XCircle className="mr-2 h-4 w-4 text-amber-600" /> Request
                changes
              </Button>
              <Button
                variant="outline"
                onClick={() => decide("REJECTED")}
                disabled={saving}
              >
                <XCircle className="mr-2 h-4 w-4 text-rose-600" /> Reject
              </Button>
              <Button
                onClick={() => decide("APPROVED")}
                disabled={
                  saving ||
                  !note.trim() ||
                  !checklist.length ||
                  checklist.some(
                    (item) => !["PASS", "NOT_APPLICABLE"].includes(item.result),
                  ) ||
                  documents.some(
                    (document) =>
                      document.validation_status !== "VALID" ||
                      !["CLEAN", "NOT_REQUIRED"].includes(document.scan_status),
                  )
                }
                className="bg-emerald-700 hover:bg-emerald-800"
              >
                <CheckCircle2 className="mr-2 h-4 w-4" /> Accept
              </Button>
            </div>
          </div>
        </div>
      ) : null}
      {selected ? (
        <div
          className="fixed inset-0 z-[60] overflow-y-auto bg-slate-950/60 p-4 md:p-8"
          role="dialog"
          aria-modal="true"
        >
          <div className="mx-auto w-full max-w-5xl overflow-hidden rounded-3xl bg-slate-50 shadow-2xl">
            <div className="flex flex-col gap-4 border-b border-slate-200 bg-white px-6 py-5 sm:flex-row sm:items-start sm:justify-between md:px-8">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-700">
                  FPO verification review
                </p>
                <h2 className="mt-1 text-2xl font-black text-slate-950">
                  {selected.fpo_name || "FPO profile"}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {selected.public_fpo_id || "Public ID pending"} ·{" "}
                  {readableStatus(selected.verification_status)}
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => setSelected(null)}
                disabled={saving}
                className="rounded-xl"
              >
                Close
              </Button>
            </div>

            <div className="grid gap-5 p-5 md:grid-cols-[1.05fr_0.95fr] md:p-8">
              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-black uppercase tracking-wider text-slate-400">
                      Organization profile
                    </p>
                    <h3 className="mt-1 text-lg font-black text-slate-950">
                      FPO details
                    </h3>
                  </div>
                  <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                    {readableStatus(selected.verification_status)}
                  </span>
                </div>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  {[
                    ["Legal / FPO name", selected.fpo_name],
                    ["Registration type", selected.registration_type],
                    ["Registration number", selected.registration_number],
                    ["Representative", selected.contact_person_name],
                    ["Email", selected.contact_email],
                    ["Phone", selected.contact_phone],
                    ["State", selected.state_name],
                    ["District", selected.district_name],
                    ["District code", selected.district_code],
                    ["Member count", selected.member_count],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        {label}
                      </p>
                      <p className="mt-1 break-words text-sm font-semibold text-slate-800">
                        {value || "Not provided"}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl bg-slate-50 p-3">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Main commodities
                    </p>
                    <p className="mt-1 text-sm text-slate-700">
                      {Array.isArray(selected.main_commodities) &&
                      selected.main_commodities.length
                        ? selected.main_commodities.join(", ")
                        : "Not provided"}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Services provided
                    </p>
                    <p className="mt-1 text-sm text-slate-700">
                      {Array.isArray(selected.services_provided) &&
                      selected.services_provided.length
                        ? selected.services_provided.join(", ")
                        : "Not provided"}
                    </p>
                  </div>
                </div>
              </section>

              <section className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-5 shadow-sm md:col-span-2">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs font-black uppercase tracking-wider text-emerald-700">
                      Commercial access configuration
                    </p>
                    <h3 className="mt-1 text-lg font-black text-slate-950">
                      Assign FPO class
                    </h3>
                    <p className="mt-1 text-sm text-slate-600">
                      Choose the operating tier that controls this FPO’s feature
                      entitlements.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      aria-label="FPO class"
                      value={classCode}
                      onChange={(event) => setClassCode(event.target.value)}
                      className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800"
                    >
                      <option value="A">Class A · Foundation</option>
                      <option value="B">Class B · Growth</option>
                      <option value="C">Class C · Commercial</option>
                    </select>
                    <Button
                      variant="outline"
                      onClick={assignClass}
                      disabled={saving}
                      className="rounded-xl border-emerald-300 bg-white"
                    >
                      {saving ? "Saving…" : "Save class"}
                    </Button>
                  </div>
                </div>
              </section>

              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-black uppercase tracking-wider text-slate-400">
                      Evidence review
                    </p>
                    <h3 className="mt-1 text-lg font-black text-slate-950">
                      Verification documents
                    </h3>
                  </div>
                  <span className="text-sm font-bold text-slate-500">
                    {documents.length} uploaded
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Open each file, confirm the evidence, then explicitly approve
                  or reject it.
                </p>
                <div className="mt-4 space-y-3">
                  {documents.length ? (
                    documents.map((document) => (
                      <article
                        key={document.document_id}
                        className="rounded-xl border border-slate-200 p-4"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="break-words text-sm font-bold text-slate-900">
                              {document.original_filename}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {readableStatus(document.document_type)} · scan{" "}
                              {readableStatus(document.scan_status)}
                            </p>
                            <p
                              className={`mt-2 text-xs font-bold ${document.validation_status === "VALID" ? "text-emerald-700" : document.validation_status === "INVALID" ? "text-rose-700" : "text-amber-700"}`}
                            >
                              Document:{" "}
                              {readableStatus(document.validation_status)}
                            </p>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewDocument(document)}
                            disabled={
                              openingDocumentId === document.document_id ||
                              validatingDocumentId === document.document_id
                            }
                          >
                            {openingDocumentId === document.document_id
                              ? "Opening…"
                              : "Open"}
                          </Button>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            onClick={() => validateDocument(document, "VALID")}
                            disabled={
                              validatingDocumentId === document.document_id
                            }
                            className="bg-emerald-700 hover:bg-emerald-800"
                          >
                            {validatingDocumentId === document.document_id
                              ? "Saving…"
                              : "Approve document"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              validateDocument(document, "INVALID")
                            }
                            disabled={
                              validatingDocumentId === document.document_id
                            }
                            className="text-rose-700"
                          >
                            Reject document
                          </Button>
                        </div>
                      </article>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-rose-300 bg-rose-50 p-4 text-sm text-rose-700">
                      No verification documents uploaded.
                    </div>
                  )}
                </div>
              </section>
            </div>

            <div className="border-t border-slate-200 bg-white px-5 py-5 md:px-8">
              <label
                className="block text-sm font-bold text-slate-700"
                htmlFor="review-note-modern"
              >
                Decision note
              </label>
              <textarea
                id="review-note-modern"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={3}
                placeholder="Add the reason for approval, rejection, or requested changes…"
                className="mt-2 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-emerald-600"
              />
              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-xs text-slate-500">
                  {documents.length &&
                  documents.every(
                    (document) =>
                      document.validation_status === "VALID" &&
                      ["CLEAN", "NOT_REQUIRED"].includes(document.scan_status),
                  )
                    ? "All uploaded documents are approved."
                    : "Approve every document before approving this FPO."}
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => decide("CHANGES_REQUIRED")}
                    disabled={saving}
                    className="rounded-xl text-amber-700"
                  >
                    Request changes
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => decide("REJECTED")}
                    disabled={saving}
                    className="rounded-xl text-rose-700"
                  >
                    Reject FPO
                  </Button>
                  <Button
                    onClick={() => decide("APPROVED")}
                    disabled={
                      saving ||
                      !note.trim() ||
                      !documents.length ||
                      documents.some(
                        (document) =>
                          document.validation_status !== "VALID" ||
                          !["CLEAN", "NOT_REQUIRED"].includes(
                            document.scan_status,
                          ),
                      )
                    }
                    className="rounded-xl bg-emerald-700 px-5 hover:bg-emerald-800"
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" /> Approve FPO
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
