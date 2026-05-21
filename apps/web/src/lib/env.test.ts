// Unit tests for runtime environment parsing. These cover the string coercions
// that are easy to get wrong when values arrive from .env files.
import { describe, expect, it } from "vitest";

import { parsePublicEnv, parseServerEnv } from "./env";

const productionEnv = {
  ENV: "production",
  AUTH_SECRET: "replace-with-a-real-32-byte-random-secret",
  AUTH_JWT_PRIVATE_KEY:
    "-----BEGIN PRIVATE KEY-----\\nfake-key-for-parser-only\\n-----END PRIVATE KEY-----",
  GOOGLE_CLIENT_ID: "google-client",
  GOOGLE_CLIENT_SECRET: "google-secret",
};

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
    expect(parsed.ENABLE_DEV_ROUTES).toBe(true);
    expect(parsed.AUTH_ALLOW_SEED_LOGIN).toBe(true);
  });

  it("preserves escaped newlines in configured JWT private keys", () => {
    const parsed = parseServerEnv({
      AUTH_JWT_PRIVATE_KEY: "line-one\\nline-two",
    });

    expect(parsed.AUTH_JWT_PRIVATE_KEY).toBe("line-one\nline-two");
  });

  it("parses disabled dev routes for server-only route guards", () => {
    const parsed = parseServerEnv({
      ENABLE_DEV_ROUTES: "false",
    });

    expect(parsed.ENABLE_DEV_ROUTES).toBe(false);
  });

  it("rejects the default auth secret in production", () => {
    expect(() =>
      parseServerEnv({
        ENV: "production",
        AUTH_SECRET: "",
      }),
    ).toThrow(/AUTH_SECRET/);
    expect(() =>
      parseServerEnv({
        ENV: "production",
        AUTH_SECRET: "dev-auth-secret-change-in-production",
      }),
    ).toThrow(/AUTH_SECRET/);
  });

  it("rejects missing JWT private keys in production", () => {
    expect(() =>
      parseServerEnv({
        ENV: "production",
        AUTH_SECRET: "replace-with-a-real-32-byte-random-secret",
        GOOGLE_CLIENT_ID: "google-client",
        GOOGLE_CLIENT_SECRET: "google-secret",
      }),
    ).toThrow(/AUTH_JWT_PRIVATE_KEY/);
  });

  it("defaults to production when NODE_ENV is production", () => {
    expect(() =>
      parseServerEnv({
        NODE_ENV: "production",
        AUTH_SECRET: "replace-with-a-real-32-byte-random-secret",
        GOOGLE_CLIENT_ID: "google-client",
        GOOGLE_CLIENT_SECRET: "google-secret",
      }),
    ).toThrow(/AUTH_JWT_PRIVATE_KEY/);
  });

  it("requires Google OAuth credentials in production", () => {
    expect(() =>
      parseServerEnv({
        ...productionEnv,
        GOOGLE_CLIENT_ID: "",
        GOOGLE_CLIENT_SECRET: "",
        NEXT_PUBLIC_USE_MOCK_GOOGLE: "true",
      }),
    ).toThrow(/GOOGLE_CLIENT_ID/);

    expect(() =>
      parseServerEnv({
        ...productionEnv,
        GOOGLE_CLIENT_SECRET: undefined,
      }),
    ).toThrow(/GOOGLE_CLIENT_SECRET/);
  });

  it("defaults dev-only affordances off in production", () => {
    const parsed = parseServerEnv(productionEnv);

    expect(parsed.AUTH_SECRET).toBe(
      "replace-with-a-real-32-byte-random-secret",
    );
    expect(parsed.AUTH_ALLOW_SEED_LOGIN).toBe(false);
    expect(parsed.ENABLE_DEV_ROUTES).toBe(false);
  });
});
