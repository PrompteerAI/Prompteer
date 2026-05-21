// Unit tests for Auth.js provider selection between real Google OAuth and the
// local Google-compatible OIDC mock.
import { describe, expect, it } from "vitest";

import { googleProvider, googleProviderMode } from "./auth-providers";

const baseEnv = {
  AUTH_MOCK_GOOGLE_DISCOVERY_URL: undefined,
  AUTH_MOCK_GOOGLE_ISSUER: "http://localhost:8000",
  AUTH_MOCK_GOOGLE_SERVER_BASE_URL: undefined,
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
      authorization: {
        url: "http://localhost:8000/o/oauth2/v2/auth",
      },
      token: "http://localhost:8000/token",
      userinfo: "http://localhost:8000/v3/userinfo",
      clientId: "mock-google-client",
    });
  });

  it("uses internal mock endpoints when server-side base URL is configured", () => {
    expect(
      googleProvider({
        ...baseEnv,
        AUTH_MOCK_GOOGLE_ISSUER: "http://localhost",
        AUTH_MOCK_GOOGLE_SERVER_BASE_URL: "http://api:8000",
      }),
    ).toMatchObject({
      issuer: "http://localhost",
      authorization: {
        url: "http://localhost/o/oauth2/v2/auth",
      },
      token: "http://api:8000/token",
      userinfo: "http://api:8000/v3/userinfo",
    });
  });

  it("derives internal mock endpoints from the discovery URL when no server base URL is configured", () => {
    expect(
      googleProvider({
        ...baseEnv,
        AUTH_MOCK_GOOGLE_ISSUER: "http://localhost",
        AUTH_MOCK_GOOGLE_DISCOVERY_URL:
          "http://api:8000/.well-known/openid-configuration",
      }),
    ).toMatchObject({
      issuer: "http://localhost",
      token: "http://api:8000/token",
      userinfo: "http://api:8000/v3/userinfo",
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
