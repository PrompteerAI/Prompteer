import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import type { OAuthConfig, Provider } from "next-auth/providers";

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
  return (
    process.env.AUTH_MOCK_GOOGLE_ISSUER || "http://localhost:8000"
  ).replace(/\/+$/, "");
}

function mockGoogleProvider(): OAuthConfig<GoogleOidcProfile> {
  const issuer = mockGoogleIssuer();

  return {
    id: "google",
    name: "Google",
    type: "oidc",
    issuer,
    wellKnown: `${issuer}/.well-known/openid-configuration`,
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
  if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
    return Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    });
  }

  return mockGoogleProvider();
}

export function seedLoginEnabled(): boolean {
  return (
    process.env.AUTH_ALLOW_SEED_LOGIN !== "false" &&
    process.env.ENV !== "production"
  );
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
    jwt({ token, user }) {
      if (user) {
        token.email = user.email;
        token.name = user.name;
        const role = (user as Partial<SeedUser>).role;
        if (typeof role === "string") {
          token.role = role;
        }
      }
      return token;
    },
  },
});
