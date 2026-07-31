import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { authApi } from "@/features/auth/api/authApi";
import { clearSession, setSession } from "@/features/auth/session";
import { apiClient } from "@/shared/api/apiClient";
import { server } from "@/test/mocks/server";

const BASE = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000";

describe("api client authentication behaviour", () => {
  beforeEach(() => {
    clearSession();
    document.cookie = "maatitrace_csrf=csrf-test; Path=/";
  });

  it("does not refresh or redirect for a public wrong-password 401", async () => {
    let refreshCalls = 0;
    server.use(
      http.post(`${BASE}/api/auth/login`, () => HttpResponse.json({ detail: { code: "INVALID_LOGIN", message: "Invalid login credentials." } }, { status: 401 })),
      http.post(`${BASE}/api/auth/refresh`, () => { refreshCalls += 1; return HttpResponse.json({}, { status: 401 }); }),
    );
    await expect(authApi.login({ identifier: "a@example.com", password: "wrong" })).rejects.toMatchObject({ status: 401, code: "INVALID_LOGIN" });
    expect(refreshCalls).toBe(0);
  });

  it("shares one refresh across concurrent protected 401 responses", async () => {
    setSession({ access_token: "old-access", expires_in_seconds: 900, user: { user_id: "1", role: "farmer" } });
    let refreshCalls = 0;
    server.use(
      http.post(`${BASE}/api/auth/refresh`, () => {
        refreshCalls += 1;
        return HttpResponse.json({ access_token: "new-access", expires_in_seconds: 900, user: { user_id: "1", role: "farmer" } });
      }),
      http.get(`${BASE}/api/a`, ({ request }) => request.headers.get("authorization") === "Bearer new-access" ? HttpResponse.json({ ok: "a" }) : HttpResponse.json({}, { status: 401 })),
      http.get(`${BASE}/api/b`, ({ request }) => request.headers.get("authorization") === "Bearer new-access" ? HttpResponse.json({ ok: "b" }) : HttpResponse.json({}, { status: 401 })),
    );
    const [a, b] = await Promise.all([
      apiClient.request("/v1/a", { authMode: "required" }),
      apiClient.request("/v1/b", { authMode: "required" }),
    ]);
    expect(a.ok).toBe("a");
    expect(b.ok).toBe("b");
    expect(refreshCalls).toBe(1);
  });
});
