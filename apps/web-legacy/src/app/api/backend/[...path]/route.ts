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
  const requestId = proxyRequestId(request);
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
      headers: gatewayHeaders(request, requestId),
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : await request.text(),
      cache: "no-store",
      redirect: "manual",
    });
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

  const headers = new Headers();
  for (const header of FORWARDED_RESPONSE_HEADERS) {
    const value = upstreamResponse.headers.get(header);
    if (value) {
      headers.set(header, value);
    }
  }
  if (!headers.has("x-request-id")) {
    headers.set("x-request-id", requestId);
  }

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers,
  });
}

function gatewayHeaders(request: NextRequest, requestId: string): Headers {
  const headers = new Headers();
  const accept = request.headers.get("accept");
  const contentType = request.headers.get("content-type");
  const cookie = request.headers.get("cookie");

  headers.set("accept", accept ?? "application/json");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (cookie) {
    headers.set("cookie", cookie);
  }
  headers.set("x-request-id", requestId);

  return headers;
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
