export const FARM_STATUS = ["NORMAL", "WATCH", "NEEDS_ATTENTION", "CRITICAL", "NO_DATA"];

export const statusLabel = (value) => String(value || "NO_DATA").replaceAll("_", " ");

export const statusClass = {
  NORMAL: "bg-emerald-50 text-emerald-700 border-emerald-200",
  WATCH: "bg-lime-50 text-lime-700 border-lime-200",
  NEEDS_ATTENTION: "bg-orange-50 text-orange-700 border-orange-200",
  CRITICAL: "bg-rose-50 text-rose-700 border-rose-200",
  NO_DATA: "bg-slate-100 text-slate-600 border-slate-200",
};

export const statusColor = {
  NORMAL: "#10b981",
  WATCH: "#84cc16",
  NEEDS_ATTENTION: "#f97316",
  CRITICAL: "#ef4444",
  NO_DATA: "#94a3b8",
};

export const getLocation = (farm) => [farm.district_name, farm.block_name, farm.village_name].filter(Boolean).join(" / ") || "Location not recorded";

export function aggregateFarms(farms, keyOf) {
  const groups = new Map();
  farms.forEach((farm) => {
    const key = keyOf(farm) || "Not recorded";
    if (!groups.has(key)) groups.set(key, { name: key, farms: 0, area: 0, alerts: 0, statuses: Object.fromEntries(FARM_STATUS.map((status) => [status, 0])) });
    const group = groups.get(key);
    group.farms += 1;
    group.area += Number(farm.area_acres || 0);
    group.alerts += Number(farm.open_alert_count || 0);
    group.statuses[farm.overall_status || "NO_DATA"] = (group.statuses[farm.overall_status || "NO_DATA"] || 0) + 1;
  });
  return [...groups.values()].map((group) => ({ ...group, concern: group.statuses.CRITICAL + group.statuses.NEEDS_ATTENTION, dominantStatus: FARM_STATUS.slice().sort((a, b) => group.statuses[b] - group.statuses[a])[0] })).sort((a, b) => b.concern - a.concern || b.farms - a.farms);
}

export function csvDownload(filename, rows) {
  const value = rows.map((row) => row.map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([value], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}
