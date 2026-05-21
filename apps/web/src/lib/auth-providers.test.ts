// Unit tests for Auth.js provider selection between real Google OAuth and the
// local Google-compatible OIDC mock.
import { describe, expect, it } from "vitest";

import { googleProvider, googleProviderMode } from "./auth-providers";

const baseEnv = {
  AUTH_MOCK_GOOGLE_DISCOVERY_URL: undefined,
  AUTH_MOCK_GOOGLE_ISSUER: "http://localhost:8000",
  GOOGLE_CLIENT_ID: undefined,
  GOOGLE_CLIENT_SECRET: undefined,
};

describe("googleProviderMode", () => {
  it("uses the mock provider when Google credentials are absent", () => {
    expect(googleProviderMode(baseEnv)).toBe("mock");
  });

  it("uses real Google OAuth only when both credentials are present", () => {
    expect(
      googleProviderMode({
        ...baseEnv,
        GOOGLE_CLIENT_ID: "google-client",
      }),
    ).toBe("mock");

    expect(
      googleProviderMode({
        ...baseEnv,
        GOOGLE_CLIENT_ID: "google-client",
        GOOGLE_CLIENT_SECRET: "google-secret",
      }),
    ).toBe("real");
  });
});

describe("googleProvider", () => {
  it("configures the local mock OIDC provider with the mock issuer", () => {
    expect(googleProvider(baseEnv)).toMatchObject({
      id: "google",
      type: "oidc",
      issuer: "http://localhost:8000",
      wellKnown: "http://localhost:8000/.well-known/openid-configuration",
      clientId: "mock-google-client",
    });
  });

  it("configures the real Google provider from GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET", () => {
    expect(
      googleProvider({
        ...baseEnv,
        GOOGLE_CLIENT_ID: "google-client",
        GOOGLE_CLIENT_SECRET: "google-secret",
      }),
    ).toMatchObject({
      id: "google",
      type: "oidc",
      issuer: "https://accounts.google.com",
      options: {
        clientId: "google-client",
        clientSecret: "google-secret",
      },
    });
  });
});
