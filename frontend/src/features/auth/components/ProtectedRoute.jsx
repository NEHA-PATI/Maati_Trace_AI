import { Navigate, Outlet, useLocation } from "react-router-dom";

import AppShell from "@/components/layout/AppShell";
import { useAuth } from "@/features/auth/context/useAuth";
import { canAccess } from "@/shared/rbac/permissions";

function AccessDenied() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
      <section className="max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-black text-slate-950">Access denied</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">Your account is signed in, but your role is not allowed to open this page.</p>
      </section>
    </main>
  );
}

export default function ProtectedRoute({ permission }) {
  const location = useLocation();
  const { user, initialising, isAuthenticated } = useAuth();

  if (initialising) {
    return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Checking your secure session…</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (permission && !canAccess(user, permission)) {
    return <AccessDenied />;
  }
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
