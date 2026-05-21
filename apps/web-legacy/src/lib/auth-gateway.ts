// Session reads for web-legacy. Auth.js remains owned by apps/web.
import { cookies } from "next/headers";

import { authGatewayOrigin } from "./env";

export interface GatewaySession {
  user?: {
    id?: string;
    email?: string | null;
    name?: string | null;
    image?: string | null;
  };
  expires?: string;
}

export async function readGatewaySession(): Promise<GatewaySession | null> {
  const cookieHeader = (await cookies()).toString();
  const response = await fetch(`${authGatewayOrigin()}/api/auth/session`, {
    headers: cookieHeader ? { cookie: cookieHeader } : undefined,
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  const session = (await response.json()) as GatewaySession | null;
  return session?.user ? session : null;
}

export function authLoginUrl(path = "/en/login"): string {
  return `${authGatewayOrigin()}${path}`;
}
