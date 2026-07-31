import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearSession,
  getAccessToken,
  getCurrentUser,
  getSessionSnapshot,
  setSession,
  subscribeSession,
} from "@/features/auth/session";

describe("memory-only session", () => {
  beforeEach(() => clearSession());

  it("stores auth state only in module memory", () => {
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    setSession({ access_token: "access", expires_in_seconds: 900, user: { user_id: "1", role: "farmer" } });
    expect(getAccessToken()).toBe("access");
    expect(getCurrentUser().role).toBe("farmer");
    expect(storageSpy).not.toHaveBeenCalled();
  });

  it("notifies subscribers and clears all state", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeSession(listener);
    setSession({ access_token: "access", expires_in_seconds: 900, user: { user_id: "1" } });
    clearSession();
    expect(listener).toHaveBeenCalledTimes(2);
    expect(getSessionSnapshot().accessToken).toBeNull();
    unsubscribe();
  });
});
