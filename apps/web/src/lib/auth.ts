import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import type { OAuthConfig, Provider } from "next-auth/providers";

const MOCK_GOOGLE_CLIENT_ID = "mock-google-client";
const MOCK_GOOGLE_CLIENT_SECRET = "mock-google-secret";

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

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [googleProvider()],
  trustHost: true,
  session: {
    strategy: "jwt",
  },
});
