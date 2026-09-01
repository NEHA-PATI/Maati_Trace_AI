/**
 * Tiny in-memory, TTL'd request cache shared across crop-diary screens.
 *
 * The crop catalogue and a freshly-loaded stage screen rarely change within a
 * session, so re-mounting a page (back/forward, tab switch) should paint from
 * memory instantly and revalidate in the background instead of showing a spinner.
 * This is display data only — never auth state — so a plain module map is fine.
 */

const store = new Map();

export function cacheGet(key, maxAgeMs = 300_000) {
  const hit = store.get(key);
  if (!hit) return undefined;
  if (Date.now() - hit.at > maxAgeMs) {
    store.delete(key);
    return undefined;
  }
  return hit.value;
}

export function cacheSet(key, value) {
  store.set(key, { value, at: Date.now() });
  return value;
}

export function cacheInvalidate(prefix) {
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) store.delete(key);
  }
}

/** Run `loader` but dedupe concurrent calls and serve a fresh cache hit. */
const inflight = new Map();
export async function cachedRequest(key, loader, maxAgeMs) {
  const cached = cacheGet(key, maxAgeMs);
  if (cached !== undefined) return cached;
  if (inflight.has(key)) return inflight.get(key);
  const promise = Promise.resolve()
    .then(loader)
    .then((value) => cacheSet(key, value))
    .finally(() => inflight.delete(key));
  inflight.set(key, promise);
  return promise;
}
