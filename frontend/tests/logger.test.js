import { describe, expect, it, vi } from "vitest";

vi.mock("@/app/config/environment", () => ({ environment: { logLevel: "debug" } }));
import { logger } from "@/shared/logging/logger";

describe("frontend logger", () => {
  it("redacts sensitive fields", () => {
    const spy = vi.spyOn(console, "info").mockImplementation(() => {});
    logger.info("test", { password: "secret", nested: { access_token: "token", safe: "ok" } });
    const line = spy.mock.calls[0][0];
    expect(line).not.toContain("secret");
    expect(line).not.toContain('"token"');
    expect(line).toContain("[REDACTED]");
    expect(line).toContain("ok");
  });
});
