import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/context/useAuth";
import FpoLifecycleBoundary from "./FpoLifecycleBoundary";

export default function FpoProvisioningRoute() {
  const { user, initialising, isAuthenticated } = useAuth();
  if (initialising) return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Checking your secure session…</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role === "admin") return <Navigate to="/admin/fpo" replace />;
  if (!user || user.role !== "fpo") return <Navigate to="/" replace />;
  return <FpoLifecycleBoundary><Outlet /></FpoLifecycleBoundary>;
}
