import type { Session } from "next-auth";
import { type NextRequest } from "next/server";

import { auth } from "@/lib/auth";
import { encodeAuthJwt } from "@/server/auth-jwt";

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

async function forwardToApi(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const session = await auth();
  if (!session?.user?.email) {
    return problemResponse({
      status: 401,
      title: "Unauthorized",
      detail: "Sign in before calling the API.",
      code: "unauthorized",
      instance: request.nextUrl.pathname,
    });
  }

  const upstreamResponse = await fetch(
    upstreamUrl(request, await context.params),
    {
      method: request.method,
      headers: upstreamHeaders(request, session),
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store",
    },
  );

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

function upstreamUrl(request: NextRequest, params: { path: string[] }): URL {
  const base = (
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    ""
  ).replace(/\/+$/, "");
  const fallbackBase = base || "http://localhost:8000/api/v1";
  const encodedPath = params.path.map(encodeURIComponent).join("/");
  const url = new URL(`${fallbackBase}/${encodedPath}`);
  url.search = request.nextUrl.search;
  return url;
}

function upstreamHeaders(request: NextRequest, session: Session): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  headers.set("accept", accept ?? "application/json");
  headers.set("authorization", `Bearer ${apiTokenForSession(session)}`);
  return headers;
}

function apiTokenForSession(session: Session): string {
  return encodeAuthJwt({
    token: {
      sub: session.user?.email ?? "unknown",
      email: session.user?.email ?? undefined,
      name: session.user?.name ?? undefined,
    },
    maxAge: 5 * 60,
    salt: "api-proxy",
    secret: process.env.AUTH_SECRET ?? "dev-auth-secret-change-in-production",
  });
}

function problemResponse(input: {
  status: number;
  title: string;
  detail: string;
  code: string;
  instance: string;
}): Response {
  return Response.json(
    {
      type: `https://prompteer.dev/errors/${input.code.replaceAll("_", "-")}`,
      title: input.title,
      status: input.status,
      detail: input.detail,
      instance: input.instance,
      code: input.code,
      request_id: null,
    },
    {
      status: input.status,
      headers: { "content-type": "application/problem+json" },
    },
  );
}
