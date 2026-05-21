// Auth.js provider configuration. Uses real Google OAuth when credentials are
// present, otherwise routes login through the local mock OIDC server.
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import type { OAuthConfig, Provider } from "next-auth/providers";

import { getServerEnv } from "@/lib/env";
import { decodeAuthJwt, encodeAuthJwt } from "@/server/auth-jwt";

const MOCK_GOOGLE_CLIENT_ID = "mock-google-client";
const MOCK_GOOGLE_CLIENT_SECRET = "mock-google-secret";

interface SeedUser {
  id: string;
  email: string;
  name: string;
  role: "admin" | "user";
}

const SEED_USERS: Record<string, SeedUser> = {
  "admin@prompteer.dev": {
    id: "00000000-0000-4000-8000-000000000001",
    email: "admin@prompteer.dev",
    name: "Prompteer Admin",
    role: "admin",
  },
  "paid@prompteer.dev": {
    id: "00000000-0000-4000-8000-000000000002",
    email: "paid@prompteer.dev",
    name: "Paid Prompt Engineer",
    role: "user",
  },
  "free@prompteer.dev": {
    id: "00000000-0000-4000-8000-000000000003",
    email: "free@prompteer.dev",
    name: "Free Prompt Builder",
    role: "user",
  },
};

interface GoogleOidcProfile {
  sub: string;
  email?: string;
  email_verified?: boolean;
  name?: string;
  picture?: string;
}

function mockGoogleIssuer(): string {
  return getServerEnv().AUTH_MOCK_GOOGLE_ISSUER.replace(/\/+$/, "");
}

function mockGoogleWellKnown(issuer: string): string {
  return (
    getServerEnv().AUTH_MOCK_GOOGLE_DISCOVERY_URL ??
    `${issuer}/.well-known/openid-configuration`
  ).replace(/\/+$/, "");
}

function mockGoogleProvider(): OAuthConfig<GoogleOidcProfile> {
  const issuer = mockGoogleIssuer();

  return {
    id: "google",
    name: "Google",
    type: "oidc",
    issuer,
    wellKnown: mockGoogleWellKnown(issuer),
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

function googleProvider(): Provider {
  const serverEnv = getServerEnv();
  if (serverEnv.GOOGLE_CLIENT_ID && serverEnv.GOOGLE_CLIENT_SECRET) {
    return Google({
      clientId: serverEnv.GOOGLE_CLIENT_ID,
      clientSecret: serverEnv.GOOGLE_CLIENT_SECRET,
    });
  }

  return mockGoogleProvider();
}

export function seedLoginEnabled(): boolean {
  const serverEnv = getServerEnv();
  return serverEnv.AUTH_ALLOW_SEED_LOGIN && serverEnv.ENV !== "production";
}

export function getSeedUser(email: string): SeedUser | undefined {
  return SEED_USERS[email.toLowerCase()];
}

function seedLoginProvider(): Provider {
  return Credentials({
    id: "seed",
    name: "Seed demo user",
    credentials: {
      email: { label: "Email", type: "email" },
    },
    authorize(credentials) {
      if (!seedLoginEnabled()) {
        return null;
      }
      const email =
        typeof credentials?.email === "string"
          ? credentials.email.toLowerCase()
          : "";
      return getSeedUser(email) ?? null;
    },
  });
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [googleProvider(), seedLoginProvider()],
  trustHost: true,
  session: {
    strategy: "jwt",
  },
  jwt: {
    encode: encodeAuthJwt,
    decode: decodeAuthJwt,
  },
  callbacks: {
    jwt({ token, user, account }) {
      if (user) {
        token.sub = account?.providerAccountId ?? user.id;
        token.email = user.email;
        token.name = user.name;
        const role = (user as Partial<SeedUser>).role;
        if (typeof role === "string") {
          token.role = role;
        }
      }
      return token;
    },
    session({ session, token }) {
      if (session.user && typeof token.sub === "string") {
        session.user.id = token.sub;
      }
      return session;
    },
  },
});
