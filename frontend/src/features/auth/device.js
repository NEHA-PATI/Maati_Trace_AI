const DEVICE_KEY = "maatitrace_device_id";

function createDeviceId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  globalThis.crypto?.getRandomValues?.(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

export function getDeviceId() {
  try {
    const existing = localStorage.getItem(DEVICE_KEY);
    if (existing) return existing;
    const created = createDeviceId();
    localStorage.setItem(DEVICE_KEY, created);
    return created;
  } catch {
    return createDeviceId();
  }
}
