// Unit tests for runtime environment parsing. These cover the string coercions
// that are easy to get wrong when values arrive from .env files.
import { describe, expect, it } from "vitest";

import { parsePublicEnv, parseServerEnv } from "./env";

describe("parsePublicEnv", () => {
  it("parses explicit false-like strings as false", () => {
    const parsed = parsePublicEnv({
      NEXT_PUBLIC_USE_MOCK_GOOGLE: "false",
    });

    expect(parsed.NEXT_PUBLIC_USE_MOCK_GOOGLE).toBe(false);
  });

  it("defaults the mock Google flag to true when absent", () => {
    const parsed = parsePublicEnv({});

    expect(parsed.NEXT_PUBLIC_USE_MOCK_GOOGLE).toBe(true);
    expect(parsed.NEXT_PUBLIC_APP_VERSION).toBe("0.1.0");
  });

  it("rejects malformed public API URLs", () => {
    expect(() =>
      parsePublicEnv({
        NEXT_PUBLIC_API_URL: "localhost:8000/api/v1",
      }),
    ).toThrow();
  });
});

describe("parseServerEnv", () => {
  it("normalizes blank optional credentials to undefined", () => {
    const parsed = parseServerEnv({
      GOOGLE_CLIENT_ID: "",
      GOOGLE_CLIENT_SECRET: "   ",
      AUTH_MOCK_GOOGLE_DISCOVERY_URL: "",
    });

    expect(parsed.GOOGLE_CLIENT_ID).toBeUndefined();
    expect(parsed.GOOGLE_CLIENT_SECRET).toBeUndefined();
    expect(parsed.AUTH_MOCK_GOOGLE_DISCOVERY_URL).toBeUndefined();
  });

  it("defaults the application version for log metadata", () => {
    const parsed = parseServerEnv({});

    expect(parsed.APP_VERSION).toBe("0.1.0");
  });

  it("preserves escaped newlines in configured JWT private keys", () => {
    const parsed = parseServerEnv({
      AUTH_JWT_PRIVATE_KEY: "line-one\\nline-two",
    });

    expect(parsed.AUTH_JWT_PRIVATE_KEY).toBe("line-one\nline-two");
  });
});
