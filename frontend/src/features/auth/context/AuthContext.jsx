import { createContext, useCallback, useEffect, useMemo, useState } from "react";

import { authApi } from "@/features/auth/api/authApi";
import {
  clearSession,
  getSessionSnapshot,
  setSession,
  subscribeSession,
} from "@/features/auth/session";
import { logger } from "@/shared/logging/logger";

export const AuthContext = createContext(null);
let bootstrapPromise = null;

function bootstrapSession() {
  if (!bootstrapPromise) {
    bootstrapPromise = authApi.refresh().finally(() => {
      bootstrapPromise = null;
    });
  }
  return bootstrapPromise;
}

export function AuthProvider({ children }) {
  const [snapshot, setSnapshot] = useState(() => getSessionSnapshot());
  const [initialising, setInitialising] = useState(true);

  useEffect(() => subscribeSession(setSnapshot), []);

  useEffect(() => {
    let active = true;
    bootstrapSession()
      .catch((error) => {
        clearSession();
        logger.info("auth_bootstrap_guest", {
          code: error?.code,
          status: error?.status,
          correlationId: error?.correlationId,
        });
      })
      .finally(() => {
        if (active) setInitialising(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const adoptAuthResponse = useCallback((response) => {
    setSession(response);
    return response.user;
  }, []);

  const passwordLogin = useCallback(async (payload) => adoptAuthResponse(await authApi.login(payload)), [adoptAuthResponse]);
  const googleLogin = useCallback(async (credential) => adoptAuthResponse(await authApi.googleLogin(credential)), [adoptAuthResponse]);
  const refreshSession = useCallback(async () => adoptAuthResponse(await authApi.refresh()), [adoptAuthResponse]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
      clearSession();
    } catch (error) {
      logger.warn("logout_server_call_failed", {
        code: error?.code,
        status: error?.status,
        correlationId: error?.correlationId,
      });
      throw error;
    }
  }, []);

  const logoutAll = useCallback(async () => {
    try {
      await authApi.logoutAll();
      clearSession();
    } catch (error) {
      logger.warn("logout_all_server_call_failed", {
        code: error?.code,
        status: error?.status,
        correlationId: error?.correlationId,
      });
      throw error;
    }
  }, []);

  const value = useMemo(() => ({
    accessToken: snapshot.accessToken,
    user: snapshot.user,
    initialising,
    isAuthenticated: Boolean(snapshot.accessToken && snapshot.user),
    adoptAuthResponse,
    passwordLogin,
    googleLogin,
    refreshSession,
    logout,
    logoutAll,
  }), [
    snapshot.accessToken,
    snapshot.user,
    initialising,
    adoptAuthResponse,
    passwordLogin,
    googleLogin,
    refreshSession,
    logout,
    logoutAll,
  ]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
