import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  Users,
  MapPin,
  Hexagon,
  BarChart3,
  FileUp,
  Plus,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import StatStrip from "@/components/ui-custom/StatStrip";
import PipelineStepper from "@/components/ui-custom/PipelineStepper";
import NotificationStack from "@/components/ui-custom/NotificationStack";
import VerificationStamp from "@/components/ui-custom/VerificationStamp";
import FarmPointerMap from "@/components/ui-custom/FarmPointerMap";
import {
  getFpo,
  getFpoBootstrapStatus,
  getFpoFarmers,
  getFpoFarms,
  getFpoSummary,
  getMyFpo,
  getFpoPortfolioReport,
  getFpoOperationalAlerts,
  acknowledgeFpoAlert,
  getFpoRelationships,
  decideFpoRelationship,
} from "@/lib/api/fpo";

export default function FpoDashboard() {
  const { fpoId } = useParams();
  const location = useLocation();
  const isSelfRoute = location.pathname === "/fpo/me";

  const [fpo, setFpo] = useState(null);
  const [summary, setSummary] = useState(null);
  const [farmers, setFarmers] = useState([]);
  const [farms, setFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bootstrapStatus, setBootstrapStatus] = useState(null);
  const [portfolioReport, setPortfolioReport] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [relationshipRequests, setRelationshipRequests] = useState([]);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");
      try {
        let baseFpo;
        try {
          baseFpo = isSelfRoute ? await getMyFpo() : await getFpo(fpoId);
        } catch (profileError) {
          if (!isSelfRoute) throw profileError;
          const status = await getFpoBootstrapStatus();
          if (status.status !== "READY") {
            setBootstrapStatus(status);
            window.setTimeout(loadDashboard, 2500);
            return;
          }
          throw profileError;
        }
        setBootstrapStatus(null);
        const [
          summaryPayload,
          farmersPayload,
          farmsPayload,
          reportPayload,
          alertsPayload,
          relationshipPayload,
        ] = await Promise.all([
          getFpoSummary(baseFpo.fpo_id).catch(() => null),
          getFpoFarmers(baseFpo.fpo_id).catch(() => []),
          getFpoFarms(baseFpo.fpo_id).catch(() => []),
          getFpoPortfolioReport().catch(() => null),
          getFpoOperationalAlerts("OPEN").catch(() => []),
          getFpoRelationships().catch(() => []),
        ]);

        if (cancelled) return;
        setFpo(baseFpo);
        setSummary(summaryPayload);
        setFarmers(farmersPayload || []);
        setFarms(farmsPayload || []);
        setPortfolioReport(reportPayload);
        setAlerts(alertsPayload || []);
        setRelationshipRequests(
          (relationshipPayload?.items || relationshipPayload || []).filter(
            (item) => item.status === "PENDING_FPO_ACCEPTANCE",
          ),
        );
      } catch (err) {
        if (cancelled) return;
        setError(
          typeof err?.message === "string"
            ? err.message
            : "Unable to load FPO dashboard.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [fpoId, isSelfRoute]);

  async function decideFarmRequest(relationshipId, decision) {
    try {
      await decideFpoRelationship(relationshipId, decision);
      setRelationshipRequests((items) =>
        items.filter((item) => item.relationship_id !== relationshipId),
      );
    } catch (requestError) {
      setError(
        requestError?.message ||
          "The farm request decision could not be saved.",
      );
    }
  }

  const farmerRows = useMemo(
    () =>
      (farmers || []).map((farmer) => {
        const farmerFarms = farms.filter(
          (farm) => farm.farmer_id === farmer.farmer_id,
        );
        const hectares = farmerFarms.reduce(
          (sum, farm) => sum + Number(farm.area_acres || 0),
          0,
        );
        return {
          id: farmer.farmer_id,
          name: farmer.full_name || "Unnamed farmer",
          village: farmer.village_name || "Village unavailable",
          block: farmer.block_name || "Block unavailable",
          farms: farmerFarms.length,
          hectares,
          status: farmer.is_active ? "active" : "pending",
        };
      }),
    [farmers, farms],
  );

  const blockCoverage = useMemo(() => {
    const grouped = new Map();
    farmerRows.forEach((row) => {
      const key = row.block || "Unmapped";
      if (!grouped.has(key)) {
        grouped.set(key, {
          block: key,
          farmers: 0,
          farms: 0,
          hectares: 0,
          coverage: 0,
        });
      }
      const bucket = grouped.get(key);
      bucket.farmers += 1;
      bucket.farms += row.farms;
      bucket.hectares += row.hectares;
    });
    return Array.from(grouped.values()).map((bucket) => ({
      ...bucket,
      coverage: Math.min(
        100,
        Math.round((bucket.farms / Math.max(bucket.farmers, 1)) * 20),
      ),
    }));
  }, [farmerRows]);

  const totalArea = useMemo(
    () => farms.reduce((sum, farm) => sum + Number(farm.area_acres || 0), 0),
    [farms],
  );

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 p-4 md:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold text-gray-800">
            FPO Command Center
          </h1>
          <p className="mt-0.5 text-xs font-medium uppercase tracking-wider text-gray-400">
            {fpo
              ? `${fpo.fpo_name} - ${fpo.district_name}, ${fpo.state_name}`
              : "Farmer Producer Organisation"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/farm-register">
            <Button
              size="sm"
              className="h-9 rounded-xl bg-emerald-600 text-xs font-semibold hover:bg-emerald-700"
            >
              <Plus className="mr-1 h-3.5 w-3.5" />
              Register Farm
            </Button>
          </Link>
          <Link to="/bulk-upload">
            <Button
              size="sm"
              variant="outline"
              className="h-9 rounded-xl border-gray-200 text-xs font-semibold hover:bg-gray-50"
            >
              <FileUp className="mr-1 h-3.5 w-3.5 text-amber-500" />
              Bulk Upload
            </Button>
          </Link>
          <Link
            to="/fpo/relationships"
            className="rounded-xl border border-gray-200 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
          >
            Farmer requests
          </Link>
        </div>
      </div>

      {loading && (
        <div className="rounded-2xl border border-gray-100 bg-white p-6 text-sm text-gray-500 shadow-sm">
          Loading FPO dashboard...
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-rose-100 bg-rose-50 p-6 text-sm text-rose-600 shadow-sm">
          {error}
        </div>
      )}

      {!loading && !error && !fpo && bootstrapStatus && (
        <div className="rounded-2xl border border-amber-100 bg-amber-50 p-6 text-sm text-amber-800 shadow-sm">
          <p className="font-semibold">Preparing your FPO workspace</p>
          <p className="mt-1 leading-6">
            Your account is ready. We are creating your organisation profile and
            will open the dashboard automatically.
          </p>
          <p className="mt-3 text-xs font-semibold uppercase tracking-wider text-amber-700">
            Status: {bootstrapStatus.status}
          </p>
        </div>
      )}

      <StatStrip
        items={[
          {
            label: "Registered Farmers",
            value: farmerRows.length,
            icon: Users,
          },
          { label: "Total Farms", value: farms.length, icon: MapPin },
          {
            label: "Total Area",
            value: totalArea.toFixed(1),
            unit: "ac",
            icon: Hexagon,
          },
          {
            label: "Active Blocks",
            value: blockCoverage.length,
            icon: Hexagon,
          },
          {
            label: "Pending Actions",
            value: Math.max(
              0,
              farmerRows.filter((item) => item.status !== "active").length,
            ),
            icon: AlertTriangle,
          },
        ]}
      />

      {portfolioReport || alerts.length ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm lg:col-span-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">
                  Portfolio report
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Consent-backed relationship health
                </p>
              </div>
              <BarChart3 className="h-5 w-5 text-emerald-600" />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                [
                  "Active members",
                  portfolioReport?.relationships?.active_farmers || 0,
                ],
                [
                  "Pending requests",
                  portfolioReport?.relationships?.pending_relationships || 0,
                ],
                [
                  "Linked profiles",
                  portfolioReport?.relationships?.linked_profiles || 0,
                ],
                ["Open alerts", portfolioReport?.alerts?.open_alerts || 0],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="mt-1 text-xl font-black text-gray-900">
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-amber-100 bg-amber-50 p-5 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-700">
              Operational alerts
            </p>
            {alerts.length ? (
              <div className="mt-3 space-y-3">
                {alerts.slice(0, 3).map((alert) => (
                  <div
                    key={alert.alert_id}
                    className="rounded-xl bg-white/80 p-3"
                  >
                    <p className="text-sm font-bold text-gray-900">
                      {alert.title}
                    </p>
                    <p className="mt-1 text-xs text-gray-600">
                      {alert.message}
                    </p>
                    <button
                      type="button"
                      className="mt-2 text-xs font-bold text-emerald-700"
                      onClick={async () => {
                        await acknowledgeFpoAlert(alert.alert_id);
                        setAlerts((items) =>
                          items.filter(
                            (item) => item.alert_id !== alert.alert_id,
                          ),
                        );
                      }}
                    >
                      Acknowledge
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-amber-800">No open alerts.</p>
            )}
          </div>
        </div>
      ) : null}

      {!loading && !error && relationshipRequests.length > 0 ? (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-700">
                Farm access inbox
              </p>
              <h2 className="mt-1 text-lg font-black text-gray-900">
                {relationshipRequests.length} farm request
                {relationshipRequests.length === 1 ? "" : "s"} need review
              </h2>
              <p className="mt-1 text-sm text-amber-900">
                Review the exact land parcel shared by each farmer. Other farms
                remain private.
              </p>
            </div>
            <Link
              to="/fpo/relationships"
              className="rounded-xl bg-emerald-700 px-3 py-2 text-xs font-black text-white hover:bg-emerald-800"
            >
              Open full inbox
            </Link>
          </div>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {relationshipRequests.slice(0, 4).map((item) => (
              <article
                key={item.relationship_id}
                className="rounded-2xl border border-amber-200 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-black text-gray-900">
                      {item.full_name || "Farmer"}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      {item.farm_name || "Farm parcel"} ·{" "}
                      {item.area_acres ?? "—"} acres
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      {item.farm_district_name ||
                        item.district_name ||
                        "District pending"}
                      ,{" "}
                      {item.farm_state_name ||
                        item.state_name ||
                        "State pending"}
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-black uppercase text-amber-800">
                    Pending
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      window.location.assign(
                        `/fpo/farmers/${item.farmer_id}/farms/${item.farm_id}/intelligence`,
                      )
                    }
                    disabled={!item.farm_id}
                  >
                    View farm
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      decideFarmRequest(item.relationship_id, "REJECTED")
                    }
                  >
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    onClick={() =>
                      decideFarmRequest(item.relationship_id, "ACTIVE")
                    }
                    className="bg-emerald-700 hover:bg-emerald-800"
                  >
                    Accept
                  </Button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">
            System Pipeline Status
          </span>
          <VerificationStamp label="OPERATIONAL" type="success" compact />
        </div>
        <PipelineStepper
          steps={[
            "Location",
            "Farmer",
            "Boundary",
            "H3 Grid",
            "Satellite",
            "Raster",
            "Intelligence",
          ]}
          currentStep={summary ? 7 : 5}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <MapPin className="h-4 w-4 text-emerald-500" />
                Farm Pointers
              </span>
              <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">
                {farms.length} farms
              </span>
            </div>
            <div className="p-3">
              <FarmPointerMap
                farms={farms}
                selectedFarmId={null}
                onFarmClick={(farm) =>
                  window.location.assign(`/land/${farm.farm_id}`)
                }
                showBoundaries={false}
                height={420}
                userRole="fpo"
                emptyMessage="No farms are linked to this FPO yet."
              />
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <Users className="h-4 w-4 text-blue-500" />
                Recent Farmer Registrations
              </span>
              <Link
                to="/my-fpo"
                className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-600 hover:underline"
              >
                View All
                <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Farmer ID
                    </th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Name
                    </th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Village
                    </th>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Block
                    </th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Farms
                    </th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Area
                    </th>
                    <th className="px-4 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {farmerRows.map((row) => (
                    <tr
                      key={row.id}
                      className="border-b border-gray-50 last:border-0 transition-colors hover:bg-gray-50/60"
                    >
                      <td className="px-4 py-2.5 font-bold text-gray-700">
                        {row.id}
                      </td>
                      <td className="px-4 py-2.5">
                        <Link
                          to={`/farmers/${row.id}`}
                          className="font-medium text-emerald-600 hover:underline"
                        >
                          {row.name}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5 text-gray-500">
                        {row.village}
                      </td>
                      <td className="px-4 py-2.5 text-gray-500">{row.block}</td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">
                        {row.farms}
                      </td>
                      <td className="px-4 py-2.5 text-right font-bold text-gray-700">
                        {row.hectares.toFixed(1)}
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <VerificationStamp
                          label={row.status.toUpperCase()}
                          type={row.status === "active" ? "success" : "pending"}
                          compact
                        />
                      </td>
                    </tr>
                  ))}
                  {!loading && !error && farmerRows.length === 0 && (
                    <tr>
                      <td
                        colSpan="7"
                        className="px-4 py-6 text-center text-sm text-gray-500"
                      >
                        No farmers are linked to this FPO yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <BarChart3 className="h-4 w-4 text-violet-500" />
                Block-wise Coverage
              </span>
            </div>
            <div className="space-y-4 p-5">
              {blockCoverage.map((block) => (
                <div key={block.block} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-gray-700">
                      {block.block}
                    </span>
                    <div className="flex items-center gap-3 text-[10px] font-medium text-gray-400">
                      <span>{block.farmers} farmers</span>
                      <span>{block.farms} farms</span>
                      <span className="font-bold text-emerald-600">
                        {block.coverage}%
                      </span>
                    </div>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${block.coverage}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, delay: 0.1 }}
                      className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                    />
                  </div>
                </div>
              ))}
              {!loading && !error && blockCoverage.length === 0 && (
                <div className="text-sm text-gray-500">
                  Block coverage will appear once farmer and farm records are
                  available.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-gray-800">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                Alerts
              </span>
              <span className="pulse-live h-2 w-2 rounded-full bg-rose-400" />
            </div>
            <div className="p-2">
              <NotificationStack limit={5} />
            </div>
          </div>

          <div className="space-y-1 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">
              Quick Actions
            </span>
            <Link
              to="/farm-register"
              className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-gray-50"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50">
                <MapPin className="h-4 w-4 text-emerald-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">
                  Register New Farm
                </p>
                <p className="text-[10px] text-gray-400">
                  Individual boundary registration
                </p>
              </div>
              <ChevronRight className="ml-auto h-3.5 w-3.5 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
            <Link
              to="/bulk-upload"
              className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-gray-50"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50">
                <FileUp className="h-4 w-4 text-amber-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">
                  Bulk CSV Upload
                </p>
                <p className="text-[10px] text-gray-400">
                  Register multiple farms at once
                </p>
              </div>
              <ChevronRight className="ml-auto h-3.5 w-3.5 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
            <Link
              to="/my-fpo"
              className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-gray-50"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50">
                <Users className="h-4 w-4 text-blue-500" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-700">
                  View All Farmers
                </p>
                <p className="text-[10px] text-gray-400">
                  Map view with population density
                </p>
              </div>
              <ChevronRight className="ml-auto h-3.5 w-3.5 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <span className="mb-3 block text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-400">
              FPO Identity
            </span>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="font-medium text-gray-400">FPO ID</span>
                <span className="font-bold text-gray-700">
                  {fpo?.fpo_id || "Pending"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-400">Region</span>
                <span className="text-gray-700">
                  {fpo ? `${fpo.district_name}, ${fpo.state_name}` : "Pending"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-gray-400">Block</span>
                <span className="text-gray-700">
                  {fpo?.block_name || "Multi-block"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-400">Status</span>
                <VerificationStamp
                  label={fpo?.is_active ? "ACTIVE" : "PENDING"}
                  type={fpo?.is_active ? "success" : "pending"}
                  compact
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
