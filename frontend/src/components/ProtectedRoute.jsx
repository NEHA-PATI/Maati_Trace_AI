import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getMe } from "@/lib/api/auth";
import { clearSession, getAccessToken, getStoredUser, saveSession } from "@/lib/auth/session";
import { canAccess } from "@/lib/rbac/permissions";
import UserNotRegisteredError from "@/components/UserNotRegisteredError";
import AppShell from "@/components/layout/AppShell";
import PostLoginLandPrompt from "@/components/onboarding/PostLoginLandPrompt";

export default function ProtectedRoute({ permission }) {
  const location = useLocation();
  const [state, setState] = useState({ loading: true, user: getStoredUser(), allowed: false });

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setState({ loading: false, user: null, allowed: false });
      return;
    }
    let cancelled = false;
    getMe()
      .then((user) => {
        if (cancelled) return;
        const session = JSON.parse(localStorage.getItem("maatitrace_session") || "null");
        if (session) saveSession({ access_token: session.accessToken, refresh_token: session.refreshToken, user });
        setState({ loading: false, user, allowed: canAccess(user, permission) });
      })
      .catch(() => {
        if (cancelled) return;
        clearSession();
        setState({ loading: false, user: null, allowed: false });
      });
    return () => { cancelled = true; };
  }, [permission]);

  if (state.loading) return <div className="min-h-screen grid place-items-center text-sm text-muted-foreground">Checking session...</div>;
  if (!state.user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (!state.allowed) return <UserNotRegisteredError />;
  return (
    <AppShell>
      <PostLoginLandPrompt user={state.user} />
      <Outlet />
    </AppShell>
  );
}
