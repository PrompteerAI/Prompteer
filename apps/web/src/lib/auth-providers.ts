// Auth.js OAuth provider selection for real Google credentials or the local
// Google-compatible OIDC mock.
import Google from "next-auth/providers/google";
import type { OAuthConfig, Provider } from "next-auth/providers";

import { getServerEnv, type ServerEnv } from "@/lib/env";

const MOCK_GOOGLE_CLIENT_ID = "mock-google-client";
const MOCK_GOOGLE_CLIENT_SECRET = "mock-google-secret";

type GoogleProviderEnv = Pick<
  ServerEnv,
  | "AUTH_MOCK_GOOGLE_DISCOVERY_URL"
  | "AUTH_MOCK_GOOGLE_ISSUER"
  | "AUTH_MOCK_GOOGLE_SERVER_BASE_URL"
  | "GOOGLE_CLIENT_ID"
  | "GOOGLE_CLIENT_SECRET"
>;

export type GoogleProviderMode = "real" | "mock";

interface GoogleOidcProfile {
  sub: string;
  email?: string;
  email_verified?: boolean;
  name?: string;
  picture?: string;
}

export function googleProviderMode(
  serverEnv: GoogleProviderEnv = getServerEnv(),
): GoogleProviderMode {
  return serverEnv.GOOGLE_CLIENT_ID && serverEnv.GOOGLE_CLIENT_SECRET
    ? "real"
    : "mock";
}

export function googleProvider(
  serverEnv: GoogleProviderEnv = getServerEnv(),
): Provider {
  if (googleProviderMode(serverEnv) === "real") {
    return Google({
      clientId: serverEnv.GOOGLE_CLIENT_ID,
      clientSecret: serverEnv.GOOGLE_CLIENT_SECRET,
    });
  }

  return mockGoogleProvider(serverEnv);
}

function mockGoogleProvider(
  serverEnv: GoogleProviderEnv,
): OAuthConfig<GoogleOidcProfile> {
  const issuer = serverEnv.AUTH_MOCK_GOOGLE_ISSUER.replace(/\/+$/, "");
  const serverBaseUrl = mockGoogleServerBaseUrl(serverEnv, issuer);

  return {
    id: "google",
    name: "Google",
    type: "oidc",
    issuer,
    wellKnown: mockGoogleWellKnown(serverEnv, issuer),
    authorization: {
      url: `${issuer}/o/oauth2/v2/auth`,
      params: { scope: "openid email profile" },
    },
    token: `${serverBaseUrl}/token`,
    userinfo: `${serverBaseUrl}/v3/userinfo`,
    clientId: MOCK_GOOGLE_CLIENT_ID,
    clientSecret: MOCK_GOOGLE_CLIENT_SECRET,
    checks: ["pkce", "state", "nonce"],
    idToken: false,
    client: {
      token_endpoint_auth_method: "client_secret_basic",
    },
    profile(profile) {
      return {
        id: profile.sub,
        email: profile.email,
        name: profile.name,
        image: profile.picture,
      };
    },
  };
}

function mockGoogleWellKnown(
  serverEnv: GoogleProviderEnv,
  issuer: string,
): string {
  return (
    serverEnv.AUTH_MOCK_GOOGLE_DISCOVERY_URL ??
    `${issuer}/.well-known/openid-configuration`
  ).replace(/\/+$/, "");
}

function mockGoogleServerBaseUrl(
  serverEnv: GoogleProviderEnv,
  issuer: string,
): string {
  if (serverEnv.AUTH_MOCK_GOOGLE_SERVER_BASE_URL) {
    return serverEnv.AUTH_MOCK_GOOGLE_SERVER_BASE_URL.replace(/\/+$/, "");
  }

  if (serverEnv.AUTH_MOCK_GOOGLE_DISCOVERY_URL) {
    return serverEnv.AUTH_MOCK_GOOGLE_DISCOVERY_URL.replace(
      /\/\.well-known\/openid-configuration\/?$/,
      "",
    );
  }

  return issuer;
}
