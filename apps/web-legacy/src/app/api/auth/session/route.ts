// Session proxy for the legacy preview header.
import { type NextRequest } from "next/server";

import { authGatewayOrigin } from "@/lib/env";

export async function GET(request: NextRequest): Promise<Response> {
  const response = await fetch(`${authGatewayOrigin()}/api/auth/session`, {
    headers: gatewayHeaders(request),
    cache: "no-store",
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      "content-type":
        response.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}

function gatewayHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  if (cookie) {
    headers.set("cookie", cookie);
  }
  return headers;
}
