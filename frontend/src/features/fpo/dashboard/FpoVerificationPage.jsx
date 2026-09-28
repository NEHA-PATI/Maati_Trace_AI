import { useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFpoDocumentUploadIntent, deleteFpoVerificationDocument, finalizeFpoVerificationDocument, getFpoVerification, getFpoVerificationDocuments, submitFpoVerification, uploadFpoVerificationDocument } from "../api/fpoPortalApi";

const DOCUMENT_TYPES = [["REGISTRATION_CERTIFICATE", "Registration certificate"], ["PAN_CARD", "PAN card"], ["GST_CERTIFICATE", "GST certificate"], ["AUTHORIZED_REPRESENTATIVE_DECLARATION", "Authorised representative declaration"], ["ADDRESS_PROOF", "Registered address proof"], ["BANK_PROOF", "Bank proof / cancelled cheque"]];
const REQUIRED_DOCUMENT_TYPES = ["REGISTRATION_CERTIFICATE", "AUTHORIZED_REPRESENTATIVE_DECLARATION", "ADDRESS_PROOF"];
const MAX_BYTES = 20 * 1024 * 1024;
const readable = (value) => String(value || "PENDING").replaceAll("_", " ");

async function sha256(file) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export default function FpoVerificationPage() {
  const queryClient = useQueryClient();
  const status = useQuery({ queryKey: ["fpo-verification"], queryFn: getFpoVerification });
  const documents = useQuery({ queryKey: ["fpo-verification-documents"], queryFn: getFpoVerificationDocuments });
  const fileInput = useRef(null);
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0][0]);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const data = status.data;
  const rows = Array.isArray(documents.data) ? documents.data : [];
  const available = useMemo(() => rows.filter((item) => item.upload_status === "AVAILABLE"), [rows]);
  const scanReady = useMemo(() => available.filter((item) => ["CLEAN", "NOT_REQUIRED"].includes(item.scan_status)), [available]);
  const hasRequired = REQUIRED_DOCUMENT_TYPES.every((type) => scanReady.some((item) => item.document_type === type));
  const canSubmit = hasRequired && scanReady.length > 0 && scanReady.length === available.length;
  const submitted = ["SUBMITTED", "UNDER_REVIEW", "APPROVED"].includes(data?.verification_status);

  async function uploadDocument(event) {
    const file = event.target.files?.[0]; event.target.value = "";
    if (!file) return;
    setError(""); setNotice("");
    if (!["application/pdf", "image/jpeg", "image/png"].includes(file.type)) return setError("Only PDF, JPEG, and PNG documents are accepted.");
    if (file.size <= 0 || file.size > MAX_BYTES) return setError("Each document must be between 1 byte and 20 MB.");
    setUploading(true);
    try {
      const checksum = await sha256(file);
      const intent = await createFpoDocumentUploadIntent({ document_type: documentType, filename: file.name, mime_type: file.type, size_bytes: file.size, checksum });
      await uploadFpoVerificationDocument(intent.document_id, file, intent.upload_url);
      await finalizeFpoVerificationDocument(intent.document_id, checksum);
      await queryClient.invalidateQueries({ queryKey: ["fpo-verification-documents"] });
      setNotice(`${file.name} uploaded successfully.`);
    } catch (requestError) { setError(requestError?.message || "The document could not be uploaded."); }
    finally { setUploading(false); }
  }

  async function removeDocument(item) {
    if (!window.confirm(`Remove ${item.original_filename}?`)) return;
    setDeletingId(item.document_id); setError(""); setNotice("");
    try {
      await deleteFpoVerificationDocument(item.document_id);
      await queryClient.invalidateQueries({ queryKey: ["fpo-verification-documents"] });
      setNotice(`${item.original_filename} was removed.`);
    } catch (requestError) { setError(requestError?.message || "The document could not be removed."); }
    finally { setDeletingId(""); }
  }

  async function submit() {
    setSubmitting(true); setError(""); setNotice("");
    try { await submitFpoVerification(); await queryClient.invalidateQueries({ queryKey: ["fpo-verification"] }); setNotice("Your FPO verification request has been submitted for administrator review."); }
    catch (requestError) { setError(requestError?.message || "The verification request could not be submitted."); }
    finally { setSubmitting(false); }
  }

  return <section className="max-w-4xl space-y-5">
    <header><p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-700">FPO verification</p><h1 className="mt-2 text-3xl font-black text-slate-950">Complete verification</h1><p className="mt-2 text-sm text-slate-500">Upload your organisation evidence. An administrator validates documents after submission.</p></header>
    {notice ? <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{notice}</div> : null}
    {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div> : null}
    <section className="rounded-2xl border border-slate-200 bg-white p-6"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Current state</p><p className="mt-2 text-2xl font-black text-slate-950">{status.isLoading ? "Loading…" : readable(data?.verification_status || "PROFILE_INCOMPLETE")}</p>{data?.reviewer_note ? <p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-900">{data.reviewer_note}</p> : null}<p className="mt-4 text-sm text-slate-500">Portfolio access becomes available only after approval and an active Class A plan assignment.</p></section>
    <section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-black text-slate-950">Verification documents</h2><p className="mt-1 text-sm text-slate-500">Accepted: PDF, JPEG, PNG. Maximum: 20 MB per file.</p><p className="mt-2 text-xs font-semibold text-amber-700">Required: registration certificate, authorised representative declaration, and address proof.</p><div className="mt-5 flex flex-col gap-3 sm:flex-row"><select value={documentType} onChange={(event) => setDocumentType(event.target.value)} disabled={submitted} className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm">{DOCUMENT_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button type="button" disabled={uploading || submitted} onClick={() => fileInput.current?.click()} className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">{uploading ? "Uploading…" : "Upload document"}</button><input ref={fileInput} type="file" accept="application/pdf,image/jpeg,image/png" className="hidden" onChange={uploadDocument} /></div><div className="mt-5 space-y-3">{documents.isLoading ? <p className="text-sm text-slate-500">Loading documents…</p> : rows.length ? rows.map((item) => <div key={item.document_id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-4"><div><p className="font-bold text-slate-900">{item.original_filename}</p><p className="mt-1 text-xs text-slate-500">{readable(item.document_type)} · {readable(item.upload_status)}</p></div><div className="flex items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase ${item.validation_status === "VALID" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{readable(item.validation_status)} · {readable(item.scan_status)}</span>{!submitted ? <button type="button" aria-label={`Remove ${item.original_filename}`} title="Remove document" disabled={deletingId === item.document_id} onClick={() => removeDocument(item)} className="grid h-8 w-8 place-items-center rounded-full border border-rose-200 text-lg font-bold text-rose-600 hover:bg-rose-50 disabled:opacity-50">×</button> : null}</div></div>) : <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">No verification documents uploaded yet.</p>}</div></section>
    <section className="rounded-2xl border border-slate-200 bg-white p-6"><div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-xl font-black text-slate-950">Submit for review</h2><p className="mt-1 text-sm text-slate-500">Document validation happens in the admin workspace after submission.</p></div><button type="button" onClick={submit} disabled={submitting || !canSubmit || submitted} className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50">{submitting ? "Submitting…" : "Submit for verification"}</button></div>{!available.length ? <p className="mt-3 text-xs font-semibold text-amber-700">Upload the required documents before submitting.</p> : !hasRequired ? <p className="mt-3 text-xs font-semibold text-amber-700">The required document checklist is incomplete.</p> : !canSubmit ? <p className="mt-3 text-xs font-semibold text-amber-700">Wait for all documents to finish their safety scan.</p> : <p className="mt-3 text-xs font-semibold text-emerald-700">Ready to submit.</p>}</section>
  </section>;
}
