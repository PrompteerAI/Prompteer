// Short-lived API bearer token creation for the same-origin Next.js proxy.
// The subject mirrors the Auth.js session subject so FastAPI sees the provider id.
import type { Session } from "next-auth";

import { getServerEnv } from "../lib/env";
import { encodeAuthJwt } from "./auth-jwt";

export function apiTokenForSession(session: Session): string {
  return encodeAuthJwt({
    token: {
      sub: session.user?.id ?? session.user?.email ?? "unknown",
      email: session.user?.email ?? undefined,
      name: session.user?.name ?? undefined,
    },
    maxAge: 5 * 60,
    salt: "api-proxy",
    secret: getServerEnv().AUTH_SECRET,
  });
}
