import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID || "mock-google-client",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "mock-google-secret"
    })
  ],
  trustHost: true,
  session: {
    strategy: "jwt"
  }
});
