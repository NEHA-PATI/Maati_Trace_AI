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

        <div className="mb-6 overflow-x-auto rounded-2xl border border-slate-200 bg-slate-50 p-1.5 shadow-sm" role="tablist" aria-label="Crop observation sections">
          <div className="flex min-w-max w-full gap-3">
            {TABS.map(([key, label, Icon]) => (
              <button key={key} type="button" role="tab" aria-selected={tab === key} onClick={() => setParams({ tab: key })} className={`inline-flex h-10 min-w-[150px] flex-1 items-center justify-center gap-2 rounded-xl px-4 text-sm font-bold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${tab === key ? 'bg-emerald-700 text-white shadow-sm' : 'text-slate-600 hover:bg-white hover:text-emerald-700'}`}>
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
