import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  getMe,
  login,
  loginWithGoogle,
  logout as logoutApi,
  refresh as refreshApi,
} from "@/lib/api/auth";

const SESSION_STORAGE_KEY = "maatitrace_session";

const AuthContext = createContext(null);

function normalizeSession(authResponse) {
  return {
    accessToken:
      authResponse?.access_token ||
      authResponse?.accessToken ||
      authResponse?.token ||
      "",
    refreshToken:
      authResponse?.refresh_token ||
      authResponse?.refreshToken ||
      "",
    user: authResponse?.user || null,
  };
}

export function getDefaultRouteForRole(role) {
  const normalizedRole = String(role || "").toLowerCase();

  if (normalizedRole === "admin") return "/dashboard";
  if (normalizedRole === "fpo") return "/fpo/dashboard";
  if (normalizedRole === "farmer") return "/farmer/dashboard";

  return "/dashboard";
}

export function saveSession(authResponse) {
  const session = normalizeSession(authResponse);

  if (!session.accessToken) {
    throw new Error("Login succeeded but access token was missing.");
  }

  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  return session;
}

export function readSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => readSession());
  const [user, setUser] = useState(() => readSession()?.user || null);
  const [initializing, setInitializing] = useState(true);

  const isAuthenticated = Boolean(session?.accessToken);

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      if (!session?.accessToken) {
        setInitializing(false);
        return;
      }

      try {
        const me = await getMe();
        if (!cancelled) {
          setUser(me?.user || me);
        }
      } catch {
        clearSession();
        if (!cancelled) {
          setSession(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setInitializing(false);
        }
      }
    }

    loadUser();

    return () => {
      cancelled = true;
    };
  }, [session?.accessToken]);

  async function passwordLogin(payload) {
    const authResponse = await login(payload);
    const nextSession = saveSession(authResponse);

    setSession(nextSession);
    setUser(nextSession.user);

    return nextSession.user;
  }

  async function googleLogin(credential) {
    const authResponse = await loginWithGoogle(credential);
    const nextSession = saveSession(authResponse);

    setSession(nextSession);
    setUser(nextSession.user);

    return nextSession.user;
  }

  async function refreshSession() {
    if (!session?.refreshToken) {
      clearSession();
      setSession(null);
      setUser(null);
      return null;
    }

    const authResponse = await refreshApi(session.refreshToken);
    const nextSession = saveSession(authResponse);

    setSession(nextSession);
    setUser(nextSession.user);

    return nextSession;
  }

  async function logout() {
    const refreshToken = session?.refreshToken;

    clearSession();
    setSession(null);
    setUser(null);

    if (refreshToken) {
      try {
        await logoutApi(refreshToken);
      } catch {
        // Local logout should still succeed even if server logout fails.
      }
    }
  }

  const value = useMemo(
    () => ({
      session,
      user,
      initializing,
      isAuthenticated,
      passwordLogin,
      googleLogin,
      refreshSession,
      logout,
      getDefaultRouteForRole,
    }),
    [session, user, initializing, isAuthenticated],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}