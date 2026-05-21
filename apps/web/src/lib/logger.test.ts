// Unit tests for the server-side web logger metadata.
import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("getWebLogger", () => {
  it("creates a singleton logger with service metadata from server env", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "test");
    vi.stubEnv("APP_VERSION", "9.8.7-test");

    const { getWebLogger } = await import("./logger");
    const firstLogger = getWebLogger();
    const secondLogger = getWebLogger();

    expect(secondLogger).toBe(firstLogger);
    expect(firstLogger.level).toBe("info");
    expect(firstLogger.bindings()).toMatchObject({
      service: "prompteer-web",
      version: "9.8.7-test",
      env: "test",
    });
  });
});
