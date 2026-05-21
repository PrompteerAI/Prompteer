// Legacy-preview API proxy. It delegates auth to the primary web app's
// same-origin API gateway, preserving the Auth.js cookies from localhost.
import { type NextRequest } from "next/server";

import { authGatewayOrigin } from "@/lib/env";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "retry-after",
  "x-ratelimit-limit",
  "x-ratelimit-remaining",
  "x-ratelimit-reset",
  "x-request-id",
];

export async function GET(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToGateway(request, context);
}

export async function POST(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToGateway(request, context);
}

export async function PUT(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToGateway(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToGateway(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToGateway(request, context);
}

async function forwardToGateway(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const params = await context.params;
  const upstream = new URL(
    `/api/backend/${params.path.map(encodeURIComponent).join("/")}`,
    authGatewayOrigin(),
  );
  upstream.search = request.nextUrl.search;

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(upstream, {
      method: request.method,
      headers: gatewayHeaders(request),
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : await request.text(),
      cache: "no-store",
      redirect: "manual",
    });
  } catch {
    return Response.json(
      {
        type: "https://prompteer.dev/errors/auth-gateway-unavailable",
        title: "Bad Gateway",
        status: 502,
        detail: "The primary web auth gateway is unavailable.",
        instance: request.nextUrl.pathname,
        code: "auth_gateway_unavailable",
      },
      {
        status: 502,
        headers: { "content-type": "application/problem+json" },
      },
    );
  }

  const headers = new Headers();
  for (const header of FORWARDED_RESPONSE_HEADERS) {
    const value = upstreamResponse.headers.get(header);
    if (value) {
      headers.set(header, value);
    }
  }

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers,
  });
}

function gatewayHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  const accept = request.headers.get("accept");
  const contentType = request.headers.get("content-type");
  const cookie = request.headers.get("cookie");
  const requestId = request.headers.get("x-request-id");

  headers.set("accept", accept ?? "application/json");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (cookie) {
    headers.set("cookie", cookie);
  }
  if (requestId) {
    headers.set("x-request-id", requestId);
  }

  return headers;
}
