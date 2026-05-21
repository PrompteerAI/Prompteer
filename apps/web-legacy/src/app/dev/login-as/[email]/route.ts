// Development-only seed-login bridge. It asks apps/web to create the Auth.js
// session, copies Set-Cookie, then returns to the legacy preview.
import { NextResponse, type NextRequest } from "next/server";

import { authGatewayOrigin } from "@/lib/env";

type RouteContext = {
  params: Promise<{ email: string }>;
};

export async function GET(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const { email } = await context.params;
  const gatewayResponse = await fetch(
    `${authGatewayOrigin()}/dev/login-as/${encodeURIComponent(email)}`,
    {
      redirect: "manual",
      cache: "no-store",
    },
  );
  const locale = request.nextUrl.searchParams.get("locale") ?? "en";
  const redirectTo = new URL(`/${locale}`, request.url);
  const response = NextResponse.redirect(redirectTo);

  for (const cookie of gatewayResponse.headers.getSetCookie()) {
    response.headers.append("set-cookie", cookie);
  }

  return response;
}
