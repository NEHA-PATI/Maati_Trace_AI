import { createElement } from "react";
import { useSearchParams } from "react-router-dom";
import { Activity, AlertTriangle, Database, FileSliders, Images, ListChecks } from "lucide-react";

import CropConfigurationPage from "./CropConfigurationPage";
import CropObservationIssuesPage from "./CropObservationIssuesPage";
import CropObservationMediaVoicePage from "./CropObservationMediaVoicePage";
import CropObservationOverviewPage from "./CropObservationOverviewPage";
import CropObservationRecordsPage from "./CropObservationRecordsPage";
import CropObservationSystemPage from "./CropObservationSystemPage";

const TABS = [
  ["overview", "Overview", Activity],
  ["records", "Farmer Records", ListChecks],
  ["issues", "Issues & Review", AlertTriangle],
  ["configuration", "Configuration", FileSliders],
  ["media", "Media & Voice", Images],
  ["system", "System", Database],
];

export default function CropObservationAdminHubPage() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "overview";

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6">
          <p className="text-sm font-bold text-emerald-700">MaatiTrace Admin</p>
          <h1 className="mt-1 text-3xl font-black text-slate-950">Crop Observation</h1>
          <p className="mt-1 max-w-[900px] text-sm text-slate-600">Configuration, farmer field records, evidence, Odia/English instruction media and operational review in one module.</p>
        </div>

        <div className="mb-6 overflow-x-auto rounded-2xl border bg-white p-2 shadow-sm">
          <div className="flex min-w-max gap-1">
            {TABS.map(([key, label, Icon]) => (
              <button key={key} onClick={() => setParams({ tab: key })} className={`inline-flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-bold transition ${tab === key ? 'bg-emerald-700 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
                {createElement(Icon, { className: "h-4 w-4" })}{label}
              </button>
            ))}
          </div>
        </div>

        {tab === "overview" ? <CropObservationOverviewPage /> : null}
        {tab === "records" ? <CropObservationRecordsPage /> : null}
        {tab === "issues" ? <CropObservationIssuesPage /> : null}
        {tab === "configuration" ? <CropConfigurationPage /> : null}
        {tab === "media" ? <CropObservationMediaVoicePage /> : null}
        {tab === "system" ? <CropObservationSystemPage /> : null}
      </div>
    </div>
  );
}
