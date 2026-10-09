import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  FileText,
  LifeBuoy,
  Search,
  ShieldCheck,
  Sprout,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { getFarms } from "@/lib/api/farm";
import {
  createFpoSupportTicket,
  cancelFarmerFpoRelationship,
  discoverFpos,
  getFpoRelationshipConsentPolicy,
  getFarmerFpoRelationships,
  requestFarmerFpoRelationship,
  revokeFarmerFpoRelationship,
} from "@/lib/api/fpo";

const statusStyle = {
  ACTIVE: "bg-emerald-50 text-emerald-700",
  PENDING_FPO_ACCEPTANCE: "bg-amber-50 text-amber-700",
  REJECTED: "bg-rose-50 text-rose-700",
  REVOKED: "bg-slate-100 text-slate-600",
  CANCELLED: "bg-slate-100 text-slate-600",
};
const label = (value) => String(value || "").replaceAll("_", " ");

export default function FarmerFpoPage() {
  const [searchParams] = useSearchParams();
  const [farms, setFarms] = useState([]);
  const [fpos, setFpos] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [selectedFarm, setSelectedFarm] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [ticketOpen, setTicketOpen] = useState(false);
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketDescription, setTicketDescription] = useState("");
  const [ticketSaving, setTicketSaving] = useState(false);
  const [consentPolicy, setConsentPolicy] = useState(null);
  const [connectTarget, setConnectTarget] = useState(null);
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [optionalScopes, setOptionalScopes] = useState([]);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [farmPayload, directory, current, policy] = await Promise.all([
        getFarms(),
        discoverFpos(query),
        getFarmerFpoRelationships(),
        getFpoRelationshipConsentPolicy(),
      ]);
      const farmRows = Array.isArray(farmPayload)
        ? farmPayload
        : farmPayload?.items || [];
      setFarms(farmRows);
      setFpos(directory || []);
      setRelationships(current || []);
      setConsentPolicy(policy);
      setSelectedFarm((value) => value || searchParams.get("farm_id") || farmRows[0]?.farm_id || "");
      setError("");
    } catch (e) {
      setError(e?.message || "Unable to load your farms and FPO connections.");
    } finally {
      setLoading(false);
    }
  }, [query, searchParams]);
  useEffect(() => {
    load();
  }, [load]);
  const selected = farms.find(
    (farm) => String(farm.farm_id) === String(selectedFarm),
  );
  const farmRelationships = useMemo(
    () =>
      relationships.filter(
        (item) => String(item.farm_id) === String(selectedFarm),
      ),
    [relationships, selectedFarm],
  );
  const activeOrPending = new Set(
    farmRelationships
      .filter((item) =>
        ["ACTIVE", "PENDING_FPO_ACCEPTANCE"].includes(item.status),
      )
      .map((item) => String(item.fpo_id)),
  );
  function request(fpo) {
    if (!selectedFarm || !consentPolicy) return;
    setConsentAccepted(false);
    setOptionalScopes([]);
    setConnectTarget(fpo);
  }
  async function submitRequest() {
    if (!selectedFarm || !connectTarget || !consentAccepted || !consentPolicy) return;
    setWorking(connectTarget.fpo_id);
    try {
      const result = await requestFarmerFpoRelationship(selectedFarm, connectTarget.fpo_id, {
        accepted: true,
        policy_code: consentPolicy.policy_code,
        policy_version: consentPolicy.policy_version,
        selected_optional_scopes: optionalScopes,
      });
      const prefix = result?.already_requested
        ? "A request to this FPO was already pending. Its status has been refreshed."
        : `Your farm request was sent to ${connectTarget.fpo_name || connectTarget.display_name || "the FPO"}.`;
      setNotice(`${prefix} Track its status under Connections for this farm.`);
      setConnectTarget(null);
      await load();
    } catch (e) {
      if (e?.status === 409) {
        await load();
        const conflictMessages = {
          FPO_ALREADY_CONNECTED: "This farm is already connected to this FPO. You can connect it to other FPOs separately.",
          FPO_NOT_AVAILABLE: "This FPO is no longer available for new farm connections. Refresh the directory and choose an approved FPO.",
          FPO_CONSENT_POLICY_STALE: "The consent policy changed or is no longer published. Review the current policy and submit again.",
          FPO_CONSENT_SCOPE_INVALID: "The selected sharing permissions are no longer valid. Review consent and try again.",
        };
        setError(conflictMessages[e.code] || e.message || "The request conflicts with the farm’s current connection state. Your status has been refreshed.");
      } else {
        setError(e?.message || "The farm connection request could not be sent.");
      }
    } finally {
      setWorking("");
    }
  }
  async function cancel(item) {
    setWorking(item.relationship_id);
    try {
      await cancelFarmerFpoRelationship(item.relationship_id);
      setNotice(`Your pending request to ${item.fpo_name || "the FPO"} has been cancelled.`);
      await load();
    } catch (e) {
      setError(e?.message || "The pending request could not be cancelled.");
    } finally {
      setWorking("");
    }
  }
  async function revoke(item) {
    setWorking(item.relationship_id);
    try {
      await revokeFarmerFpoRelationship(item.farm_id, item.relationship_id);
      setNotice(`Access for ${item.fpo_name || "this FPO"} to this farm has been revoked.`);
      await load();
    } catch (e) {
      setError(e?.message || "The farm connection could not be revoked.");
    } finally {
      setWorking("");
    }
  }
  async function submitTicket() {
    setTicketSaving(true);
    try {
      await createFpoSupportTicket({
        farm_id: selectedFarm || null,
        subject: ticketSubject,
        description: ticketDescription,
        category: "ACCESS",
      });
      setTicketSubject("");
      setTicketDescription("");
      setTicketOpen(false);
      setError("");
    } catch (e) {
      setError(e?.message || "The support ticket could not be submitted.");
    } finally {
      setTicketSaving(false);
    }
  }
  return (
    <div className="min-h-screen bg-[#F6F7F2] px-4 pb-24 pt-5 md:px-8 md:py-8">
      <div className="mx-auto max-w-[1320px] space-y-6">
      <header>
        <Link
          to="/farmer/me"
          className="text-xs font-bold text-[#4B6B3A] hover:underline"
        >
          ← Back to farmer dashboard
        </Link>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-[#6E8A5D]">
              Farmer workspace
            </p>
            <h1 className="mt-2 text-3xl font-black text-[#1D2117]">Connect with an FPO</h1>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-[#687064]">
              Connect individual farms with approved FPOs. Each connection is
              farm-specific; your other farms remain private.
            </p>
          </div>
          <Button variant="outline" onClick={() => setTicketOpen(true)}>
            <LifeBuoy className="mr-2 h-4 w-4" /> Raise a concern
          </Button>
        </div>
        <Link
          to="/farmer/imported-onboarding"
          className="mt-4 inline-flex items-center rounded-xl border border-[#CFE2C4] bg-[#EEF6E9] px-4 py-2.5 text-sm font-black text-[#4B6B3A] hover:bg-[#E1F1D6]"
        >
          Review imported onboarding information
        </Link>
      </header>
      {error ? (
        <div
          role="alert"
          className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
        >
          {error}
        </div>
      ) : null}
      {notice ? <div role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-900">{notice}</div> : null}
      <section className="rounded-[24px] border border-[#E3E8DE] bg-white p-5 shadow-[0_10px_30px_rgba(43,61,35,0.05)] md:p-6">
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#E1F1D6] text-[#4B6B3A]"><Sprout className="h-5 w-5" /></span>
          <div><h2 className="text-lg font-black text-[#1D2117]">Choose a farm</h2><p className="text-xs font-medium text-[#8A9684]">One farm per connection</p></div>
        </div>
          <p className="mt-3 text-sm text-[#687064]">
          The selected farm is the only land that an FPO request can cover.
        </p>
        {loading ? (
          <div className="mt-5 grid gap-3 sm:grid-cols-2" aria-label="Loading farms">
            {[1, 2].map((item) => <div key={item} className="animate-pulse rounded-2xl border border-[#E3E8DE] bg-[#F8FAF6] p-4"><div className="h-4 w-2/3 rounded bg-[#DDE8D8]" /><div className="mt-3 h-3 w-1/2 rounded bg-[#E7EEE3]" /><div className="mt-5 h-9 w-full rounded-xl bg-[#E7EEE3]" /></div>)}
          </div>
        ) : (
          <div className="mt-5">
            {farms.length ? (
              <>
                <label htmlFor="fpo-farm-select" className="mb-2 block text-xs font-bold text-slate-600">Choose the farm for this connection</label>
                <select id="fpo-farm-select" value={selectedFarm} onChange={(event) => setSelectedFarm(event.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 outline-none focus:border-emerald-600 md:max-w-2xl">
                  {farms.map((farm) => <option key={farm.farm_id} value={farm.farm_id}>{farm.farm_name || "Unnamed farm"} · {farm.area_acres ?? "—"} acres · {[farm.village_name, farm.district_name].filter(Boolean).join(", ") || "Location pending"}</option>)}
                </select>
                <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
                  <table className="min-w-full text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-2">Farm</th><th className="px-4 py-2">Area</th><th className="px-4 py-2">Village / district</th><th className="px-4 py-2">Crop</th><th className="px-4 py-2">Status</th></tr></thead><tbody>{farms.map((farm) => <tr key={farm.farm_id} onClick={() => setSelectedFarm(String(farm.farm_id))} className={`cursor-pointer border-t border-slate-100 ${String(selectedFarm) === String(farm.farm_id) ? "bg-emerald-50" : "hover:bg-slate-50"}`}><td className="px-4 py-3 font-bold text-slate-800">{farm.farm_name || "Unnamed farm"}</td><td className="px-4 py-3">{farm.area_acres ?? "—"} ac</td><td className="px-4 py-3">{[farm.village_name, farm.district_name, farm.state_name].filter(Boolean).join(", ") || "—"}</td><td className="px-4 py-3">{farm.crop_name || farm.crop_code || "Not set"}</td><td className="px-4 py-3">{farm.is_active === false ? "Inactive" : "Active"}</td></tr>)}</tbody></table>
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-500">
                Register a farm before connecting it to an FPO.
              </p>
            )}
          </div>
        )}
      </section>
      {selected ? (
        <section className="rounded-[24px] border border-[#CFE2C4] bg-[#EEF6E9] p-5 md:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-[#6E8A5D]">
                Selected farm
              </p>
              <h2 className="mt-1 text-xl font-black text-[#1D2117]">
                {selected.farm_name || "Unnamed farm"}
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                {selected.area_acres ?? "—"} acres ·{" "}
                {selected.village_name || "Village pending"} ·{" "}
                {selected.district_name || "District pending"}
              </p>
            </div>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-[#4B6B3A]">
              Farm-only sharing
            </span>
          </div>
          <div className="mt-4 flex items-start gap-3 rounded-2xl border border-[#DCE8D5] bg-white p-4 text-sm text-[#687064]">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#4B6B3A]" />
            <p>
              This connection does not grant access to your other farms. You can
              revoke this farm’s access at any time.
            </p>
          </div>
        </section>
      ) : null}
      <section className="rounded-[24px] border border-[#E3E8DE] bg-white p-5 shadow-[0_10px_30px_rgba(43,61,35,0.05)] md:p-6">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-black text-slate-950">
              Connections for this farm
            </h2>
            <p className="text-sm text-slate-500">
              You may connect different farms to different FPOs.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-500">
            <FileText className="h-4 w-4" />
            {farmRelationships.length} record
            {farmRelationships.length === 1 ? "" : "s"}
          </div>
        </div>
        <div className="mt-4 space-y-3">
          {farmRelationships.length ? (
            farmRelationships.map((item) => (
              <article
                key={item.relationship_id}
                className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center"
              >
                <div>
                  <p className="font-bold text-slate-900">
                  <Link to={`/farmer/farms/${item.farm_id}/fpo/${item.relationship_id}`} className="font-bold text-slate-900 hover:text-emerald-800 hover:underline">{item.fpo_name || "FPO"}</Link>
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.public_fpo_id || "ID pending"} · requested{" "}
                    {item.created_at
                      ? new Date(item.created_at).toLocaleDateString()
                      : "—"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-black uppercase ${statusStyle[item.status] || statusStyle.REVOKED}`}
                  >
                    {label(item.status)}
                  </span>
                  {item.status === "ACTIVE" ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => revoke(item)}
                      disabled={working === item.relationship_id}
                    >
                      Revoke access
                    </Button>
                  ) : null}
                  {item.status === "PENDING_FPO_ACCEPTANCE" ? <Button variant="outline" size="sm" onClick={() => cancel(item)} disabled={working === item.relationship_id}>Cancel request</Button> : null}
                </div>
              </article>
            ))
          ) : (
            <p className="rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
              No FPO is connected to this farm yet.
            </p>
          )}
        </div>
      </section>
      <section className="rounded-[24px] border border-[#E3E8DE] bg-white p-5 shadow-[0_10px_30px_rgba(43,61,35,0.05)] md:p-6">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-black text-slate-950">
              Find an approved FPO
            </h2>
            <p className="text-sm text-slate-500">
              Requests are created for{" "}
              <strong>{selected?.farm_name || "the selected farm"}</strong>.
            </p>
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              load();
            }}
            className="flex gap-2"
          >
            <div className="flex items-center rounded-xl border border-slate-300 px-3">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search FPO or district"
                className="w-40 border-0 px-2 py-2 text-sm outline-none"
              />
            </div>
            <Button type="submit" size="sm">
              Search
            </Button>
          </form>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {fpos.length ? (
            fpos.map((fpo) => (
              <article
                key={fpo.fpo_id}
                className="group rounded-2xl border border-[#E3E8DE] bg-[#FBFCF8] p-4 transition hover:-translate-y-0.5 hover:border-[#B8CEA9] hover:bg-white hover:shadow-[0_10px_24px_rgba(43,61,35,0.08)]"
              >
                <p className="font-bold text-slate-900">
                  {fpo.fpo_name || fpo.display_name || "FPO"}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {fpo.public_fpo_id || "ID pending"} ·{" "}
                  {fpo.district_name || "District pending"},{" "}
                  {fpo.state_name || "State pending"}
                </p>
                <Button
                  className="mt-4"
                  size="sm"
                  onClick={() => request(fpo)}
                  disabled={
                    !selectedFarm ||
                    Boolean(working) ||
                    activeOrPending.has(String(fpo.fpo_id)) || !consentPolicy
                  }
                >
                  {activeOrPending.has(String(fpo.fpo_id))
                    ? farmRelationships.some((item) => String(item.fpo_id) === String(fpo.fpo_id) && item.status === "ACTIVE") ? "Connected" : "Request pending"
                    : "Connect this farm"}
                </Button>
              </article>
            ))
          ) : (
            <p className="text-sm text-slate-500">
              No approved FPOs match your search.
            </p>
          )}
        </div>
      </section>
      {ticketOpen ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-emerald-700">
                  Support
                </p>
                <h2 className="text-xl font-black text-slate-950">
                  Raise a concern
                </h2>
              </div>
              <button
                type="button"
                aria-label="Close"
                onClick={() => setTicketOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="mt-3 text-sm text-slate-500">
              Tell us what needs attention about your FPO connection or farm
              access.
            </p>
            <textarea
              className="mt-4 min-h-32 w-full rounded-2xl border border-slate-300 p-3 text-sm outline-none focus:border-emerald-600"
              value={ticketDescription}
              onChange={(event) => setTicketDescription(event.target.value)}
              placeholder="Describe your concern…"
            />
            <input
              className="mt-3 w-full rounded-2xl border border-slate-300 p-3 text-sm outline-none focus:border-emerald-600"
              value={ticketSubject}
              onChange={(event) => setTicketSubject(event.target.value)}
              placeholder="Short subject"
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setTicketOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={submitTicket}
                disabled={
                  ticketSaving ||
                  ticketSubject.trim().length < 3 ||
                  ticketDescription.trim().length < 10
                }
              >
                {ticketSaving ? "Submitting…" : "Submit ticket"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
      {connectTarget ? <div className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/50 p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="fpo-consent-title" className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-black uppercase tracking-[0.16em] text-emerald-700">Review data sharing</p><h2 id="fpo-consent-title" className="mt-1 text-xl font-black text-slate-950">Connect {selected?.farm_name || "this farm"} to {connectTarget.fpo_name || connectTarget.display_name}</h2></div><button type="button" aria-label="Close" onClick={() => setConnectTarget(null)} className="rounded-full p-2 hover:bg-slate-100"><X className="h-5 w-5" /></button></div><div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700"><p><b>Farm:</b> {selected?.farm_name || "Unnamed farm"} · {selected?.area_acres ?? "—"} acres</p><p className="mt-1"><b>Location:</b> {[selected?.village_name, selected?.block_name, selected?.district_name, selected?.state_name].filter(Boolean).join(", ") || "Not provided"}</p><p className="mt-1"><b>FPO:</b> {connectTarget.public_fpo_id || ""} {connectTarget.district_name ? `· ${connectTarget.district_name}` : ""}</p></div>{consentPolicy ? <div className="mt-4"><h3 className="font-bold text-slate-900">{consentPolicy.title || "FPO data-sharing consent"}</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{consentPolicy.content}</p><div className="mt-3 rounded-xl border border-slate-200 p-4"><p className="text-xs font-black uppercase text-slate-500">Required access</p><p className="mt-2 text-sm text-slate-700">{(consentPolicy.mandatory_scopes || []).join(", ") || "No required scopes listed"}</p>{consentPolicy.optional_scopes?.length ? <div className="mt-4"><p className="text-xs font-black uppercase text-slate-500">Optional sharing (you choose)</p><div className="mt-2 space-y-2">{consentPolicy.optional_scopes.map((scope) => <label key={scope} className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={optionalScopes.includes(scope)} onChange={(event) => setOptionalScopes((current) => event.target.checked ? [...current, scope] : current.filter((value) => value !== scope))} />{label(scope)}</label>)}</div></div> : null}</div></div> : null}<label className="mt-4 flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950"><input type="checkbox" checked={consentAccepted} onChange={(event) => setConsentAccepted(event.target.checked)} className="mt-1" /><span>I have read this policy and explicitly consent to share only this farm's data with this FPO for the listed purposes. I understand I can cancel this request or revoke access later.</span></label><div className="mt-5 flex justify-end gap-2"><Button variant="outline" onClick={() => setConnectTarget(null)}>Go back</Button><Button onClick={submitRequest} disabled={!consentAccepted || Boolean(working)}>{working ? "Sending…" : "Confirm and send request"}</Button></div></section></div> : null}
      </div>
    </div>
  );
}
