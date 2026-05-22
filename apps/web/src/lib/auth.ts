// Auth.js provider configuration. Uses real Google OAuth when credentials are
// present, otherwise routes login through the local mock OIDC server.
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import type { Provider } from "next-auth/providers";

import { googleProvider } from "@/lib/auth-providers";
import { getServerEnv } from "@/lib/env";

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
  providers: authProviders(),
  trustHost: true,
  session: {
    strategy: "jwt",
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

function authProviders(): Provider[] {
  const providers: Provider[] = [googleProvider()];
  if (seedLoginEnabled()) {
    providers.push(seedLoginProvider());
  }
  return providers;
}
