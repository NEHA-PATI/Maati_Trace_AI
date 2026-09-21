import { useLocation } from "react-router-dom";

export default function FpoBreadcrumbs() {
  const location = useLocation();
  const label = location.pathname.split("/").filter(Boolean).pop()?.replaceAll("-", " ") || "dashboard";
  return <p className="mb-4 text-xs font-semibold capitalize text-slate-400">FPO / {label}</p>;
}
