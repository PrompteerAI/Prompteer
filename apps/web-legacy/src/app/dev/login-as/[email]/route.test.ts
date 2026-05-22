// Unit tests for the legacy-preview dev-login bridge. The bridge must not
// redirect as if login succeeded when the primary Auth.js app rejects login.
import { afterEach, describe, expect, it, vi } from "vitest";
import type { NextRequest } from "next/server";

type RouteContext = {
  params: Promise<{ email: string }>;
};

afterEach(() => {
  vi.resetModules();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("legacy dev login bridge", () => {
  it("returns Problem Details instead of redirecting when the auth gateway rejects login", async () => {
    vi.stubEnv("APP_URL", "http://gateway.test");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("Not found", {
          status: 404,
          headers: { "x-request-id": "req-login-404" },
        }),
      ),
    );

    const { GET } = await import("./route");
    const response = await GET(
      nextRequest(
        "http://legacy.test/dev/login-as/missing%40prompteer.dev?locale=en",
        {
          headers: { "x-request-id": "req-login-1" },
        },
      ),
      routeContext("missing@prompteer.dev"),
    );

    await expect(response.json()).resolves.toMatchObject({
      type: "https://prompteer.dev/errors/dev-login-failed",
      title: "Dev Login Failed",
      status: 404,
      detail: "The primary web auth gateway rejected the dev login request.",
      instance: "/dev/login-as/missing%40prompteer.dev",
      code: "dev_login_failed",
      request_id: "req-login-404",
    });
    expect(response.status).toBe(404);
    expect(response.headers.get("content-type")).toContain(
      "application/problem+json",
    );
    expect(response.headers.get("location")).toBeNull();
  });

  it("copies cookies and preserves the callback redirect on gateway success", async () => {
    vi.stubEnv("APP_URL", "http://gateway.test");
    const gatewayHeaders = new Headers({ "x-request-id": "req-login-ok" });
    Object.defineProperty(gatewayHeaders, "getSetCookie", {
      value: () => ["authjs.session-token=abc; Path=/; HttpOnly"],
    });
    const fetchMock = vi.fn().mockResolvedValue({
      headers: gatewayHeaders,
      status: 204,
    });
    vi.stubGlobal("fetch", fetchMock);

    const { GET } = await import("./route");
    const response = await GET(
      nextRequest(
        "http://legacy.test/dev/login-as/admin%40prompteer.dev?locale=en&callbackUrl=%2Fen%2Fbilling%3Fplan%3Dpro",
        {
          headers: { "x-request-id": "req-login-2" },
        },
      ),
      routeContext("admin@prompteer.dev"),
    );

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "http://legacy.test/en/billing?plan=pro",
    );
    expect(response.headers.get("set-cookie")).toContain(
      "authjs.session-token=abc",
    );
    expect(response.headers.get("x-request-id")).toBe("req-login-ok");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://gateway.test/dev/login-as/admin%40prompteer.dev",
    );
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(new Headers(init.headers).get("x-request-id")).toBe("req-login-2");
  });
});

function nextRequest(url: string, init: RequestInit = {}): NextRequest {
  const request = new Request(url, init) as NextRequest;
  Object.defineProperty(request, "nextUrl", { value: new URL(url) });
  return request;
}

function routeContext(email: string): RouteContext {
  return { params: Promise.resolve({ email }) };
}
