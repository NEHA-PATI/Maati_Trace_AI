import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { server } from "@/test/mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
  document.cookie = "maatitrace_csrf=; Max-Age=0; Path=/";
  vi.restoreAllMocks();
});
afterAll(() => server.close());

if (!globalThis.crypto?.randomUUID) {
  Object.defineProperty(globalThis, "crypto", {
    value: { randomUUID: () => "11111111-1111-4111-8111-111111111111", getRandomValues: (array) => array.fill(1) },
  });
}
