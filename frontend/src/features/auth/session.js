let accessToken = null;
let currentUser = null;
let expiresAt = 0;
const listeners = new Set();
const SESSION_STORAGE_KEY = "maatitrace.auth.session";

function readPersistedSession() {
  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (!parsed?.accessToken || !parsed?.user || Number(parsed.expiresAt) <= Date.now()) {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
      return;
    }
    accessToken = parsed.accessToken;
    currentUser = parsed.user;
    expiresAt = Number(parsed.expiresAt);
  } catch {
    // Storage may be unavailable or contain invalid data; the cookie refresh
    // flow remains the source of truth in that case.
  }
}

function persistSession() {
  try {
    if (accessToken && currentUser && expiresAt > 0) {
      window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({ accessToken, user: currentUser, expiresAt }));
    } else {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  } catch {
    // Keep authentication functional when browser storage is unavailable.
  }
}

function emit() {
  const snapshot = getSessionSnapshot();
  listeners.forEach((listener) => listener(snapshot));
}

export function setSession(authResponse) {
  accessToken = authResponse?.access_token || null;
  currentUser = authResponse?.user || null;
  const lifetimeSeconds = Number(authResponse?.expires_in_seconds || 0);
  expiresAt = accessToken && lifetimeSeconds > 0 ? Date.now() + lifetimeSeconds * 1000 : 0;
  persistSession();
  emit();
  return getSessionSnapshot();
}

export function clearSession() {
  accessToken = null;
  currentUser = null;
  expiresAt = 0;
  persistSession();
  emit();
}

export function getAccessToken() {
  return accessToken;
}

export function getCurrentUser() {
  return currentUser;
}

export function getSessionSnapshot() {
  return Object.freeze({ accessToken, user: currentUser, expiresAt });
}

export function isAccessTokenFresh(skewSeconds = 30) {
  return Boolean(accessToken && expiresAt > Date.now() + skewSeconds * 1000);
}

export function subscribeSession(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export const saveSession = setSession;
export const getStoredUser = getCurrentUser;

readPersistedSession();
