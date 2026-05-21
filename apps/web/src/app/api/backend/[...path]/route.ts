// Same-origin API proxy. It attaches a short-lived Auth.js JWT before
// forwarding browser requests to the FastAPI backend.
import type { Session } from "next-auth";
import { type NextRequest } from "next/server";

import { auth } from "@/lib/auth";
import { getServerEnv } from "@/lib/env";
import { apiTokenForSession } from "@/server/api-token";

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
  return forwardToApi(request, context);
}

export async function POST(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToApi(request, context);
}

export async function PUT(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToApi(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToApi(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToApi(request, context);
}

export async function HEAD(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  return forwardToApi(request, context);
}

async function forwardToApi(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const requestId = proxyRequestId(request);
  const session = await auth();
  if (!session?.user?.email) {
    return problemResponse({
      status: 401,
      title: "Unauthorized",
      detail: "Sign in before calling the API.",
      code: "unauthorized",
      instance: request.nextUrl.pathname,
      requestId,
    });
  }

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(upstreamUrl(request, await context.params), {
      method: request.method,
      headers: upstreamHeaders(request, session, requestId),
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : await request.text(),
      cache: "no-store",
    });
  } catch {
    return problemResponse({
      status: 502,
      title: "Bad Gateway",
      detail: "The API server is unavailable.",
      code: "api_unavailable",
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

function upstreamUrl(request: NextRequest, params: { path: string[] }): URL {
  const serverEnv = getServerEnv();
  const base = (
    serverEnv.API_INTERNAL_URL || serverEnv.NEXT_PUBLIC_API_URL
  ).replace(/\/+$/, "");
  const upstreamPath =
    params.path[0] === "api" && params.path[1] === "v1"
      ? params.path.slice(2)
      : params.path;
  const encodedPath = upstreamPath.map(encodeURIComponent).join("/");
  const url = new URL(`${base}/${encodedPath}`);
  url.search = request.nextUrl.search;
  return url;
}

function upstreamHeaders(
  request: NextRequest,
  session: Session,
  requestId: string,
): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  headers.set("accept", accept ?? "application/json");
  headers.set("x-request-id", requestId);
  headers.set("authorization", `Bearer ${apiTokenForSession(session)}`);
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
