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

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(upstreamUrl(request, await context.params), {
      method: request.method,
      headers: upstreamHeaders(request, session),
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store",
    });
  } catch {
    return problemResponse({
      status: 502,
      title: "Bad Gateway",
      detail: "The API server is unavailable.",
      code: "api_unavailable",
      instance: request.nextUrl.pathname,
    });
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

function upstreamHeaders(request: NextRequest, session: Session): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  headers.set("accept", accept ?? "application/json");
  const requestId = request.headers.get("x-request-id");
  if (requestId) {
    headers.set("x-request-id", requestId.slice(0, 128));
  }
  headers.set("authorization", `Bearer ${apiTokenForSession(session)}`);
  return headers;
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
