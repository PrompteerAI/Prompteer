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
  const requestId = proxyRequestId(request);
  let gatewayResponse: Response;
  try {
    gatewayResponse = await fetch(
      `${authGatewayOrigin()}/dev/login-as/${encodeURIComponent(email)}`,
      {
        headers: { "x-request-id": requestId },
        redirect: "manual",
        cache: "no-store",
      },
    );
  } catch {
    return problemResponse({
      status: 502,
      title: "Bad Gateway",
      detail: "The primary web auth gateway is unavailable.",
      code: "auth_gateway_unavailable",
      instance: request.nextUrl.pathname,
      requestId,
    });
  }

  if (gatewayResponse.status >= 400) {
    return problemResponse({
      status: gatewayResponse.status,
      title: "Dev Login Failed",
      detail: "The primary web auth gateway rejected the dev login request.",
      code: "dev_login_failed",
      instance: request.nextUrl.pathname,
      requestId:
        gatewayResponse.headers.get("x-request-id")?.trim() || requestId,
    });
  }

  const locale = request.nextUrl.searchParams.get("locale") ?? "en";
  const redirectTo = redirectTarget(request, locale);
  const response = NextResponse.redirect(redirectTo);

  for (const cookie of gatewayResponse.headers.getSetCookie()) {
    response.headers.append("set-cookie", cookie);
  }
  response.headers.set(
    "x-request-id",
    gatewayResponse.headers.get("x-request-id")?.trim() || requestId,
  );

  return response;
}

function redirectTarget(request: NextRequest, locale: string): URL {
  const callbackUrl = request.nextUrl.searchParams.get("callbackUrl");
  if (callbackUrl?.startsWith("/") && !callbackUrl.startsWith("//")) {
    return new URL(callbackUrl, request.url);
  }
  return new URL(`/${locale}`, request.url);
}

function proxyRequestId(request: NextRequest): string {
  const requestId = request.headers.get("x-request-id")?.trim();
  if (requestId) {
    return requestId.slice(0, 128);
  }
  return crypto.randomUUID();
}

function problemResponse(input: {
  status: number;
  title: string;
  detail: string;
  code: string;
  instance: string;
  requestId: string;
}): Response {
  return Response.json(
    {
      type: `https://prompteer.dev/errors/${input.code.replaceAll("_", "-")}`,
      title: input.title,
      status: input.status,
      detail: input.detail,
      instance: input.instance,
      code: input.code,
      request_id: input.requestId,
    },
    {
      status: input.status,
      headers: {
        "content-type": "application/problem+json",
        "x-request-id": input.requestId,
      },
    },
  );
}
