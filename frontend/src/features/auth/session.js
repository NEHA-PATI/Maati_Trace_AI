let accessToken = null;
let currentUser = null;
let expiresAt = 0;
const listeners = new Set();

function emit() {
  const snapshot = getSessionSnapshot();
  listeners.forEach((listener) => listener(snapshot));
}

export function setSession(authResponse) {
  accessToken = authResponse?.access_token || null;
  currentUser = authResponse?.user || null;
  const lifetimeSeconds = Number(authResponse?.expires_in_seconds || 0);
  expiresAt = accessToken && lifetimeSeconds > 0 ? Date.now() + lifetimeSeconds * 1000 : 0;
  emit();
  return getSessionSnapshot();
}

export function clearSession() {
  accessToken = null;
  currentUser = null;
  expiresAt = 0;
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
