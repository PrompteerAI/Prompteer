// Unit tests for the legacy-preview API gateway bridge. These guard request-id
// propagation because mutation UIs depend on Problem Details support metadata.
import { afterEach, describe, expect, it, vi } from "vitest";
import type { NextRequest } from "next/server";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

afterEach(() => {
  vi.resetModules();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("legacy API backend proxy", () => {
  it("returns Problem Details with the incoming request id when the auth gateway is unavailable", async () => {
    vi.stubEnv("APP_URL", "http://gateway.test");
    const fetchMock = vi.fn().mockRejectedValue(new Error("gateway down"));
    vi.stubGlobal("fetch", fetchMock);

    const { GET } = await import("./route");
    const response = await GET(
      nextRequest("http://legacy.test/api/backend/api/v1/profile", {
        headers: { "x-request-id": "req-legacy-1" },
      }),
      routeContext(["api", "v1", "profile"]),
    );

    await expect(response.json()).resolves.toMatchObject({
      type: "https://prompteer.dev/errors/auth-gateway-unavailable",
      title: "Bad Gateway",
      status: 502,
      detail: "The primary web auth gateway is unavailable.",
      instance: "/api/backend/api/v1/profile",
      code: "auth_gateway_unavailable",
      request_id: "req-legacy-1",
    });
    expect(response.status).toBe(502);
    expect(response.headers.get("content-type")).toContain(
      "application/problem+json",
    );
    expect(response.headers.get("x-request-id")).toBe("req-legacy-1");
    const [upstreamUrl, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(upstreamUrl.href).toBe(
      "http://gateway.test/api/backend/api/v1/profile",
    );
    expect(new Headers(init.headers).get("x-request-id")).toBe("req-legacy-1");
  });

  it("preserves upstream Problem Details and adds a response request-id header fallback", async () => {
    vi.stubEnv("APP_URL", "http://gateway.test");
    const problem = {
      type: "https://prompteer.dev/errors/rate-limited",
      title: "Too Many Requests",
      status: 429,
      detail: "Prompt runs are rate limited.",
      instance: "/api/v1/challenges/ch_123/run",
      code: "rate_limited",
      request_id: "req-forwarded",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(problem, {
          status: 429,
          headers: { "content-type": "application/problem+json" },
        }),
      ),
    );

    const { POST } = await import("./route");
    const response = await POST(
      nextRequest(
        "http://legacy.test/api/backend/api/v1/challenges/ch_123/run",
        {
          body: JSON.stringify({ prompt: "explain fizzbuzz" }),
          headers: {
            "content-type": "application/json",
            "x-request-id": "req-forwarded",
          },
          method: "POST",
        },
      ),
      routeContext(["api", "v1", "challenges", "ch_123", "run"]),
    );

    await expect(response.json()).resolves.toEqual(problem);
    expect(response.status).toBe(429);
    expect(response.headers.get("content-type")).toContain(
      "application/problem+json",
    );
    expect(response.headers.get("x-request-id")).toBe("req-forwarded");
  });
});

function nextRequest(url: string, init: RequestInit = {}): NextRequest {
  const request = new Request(url, init) as NextRequest;
  Object.defineProperty(request, "nextUrl", { value: new URL(url) });
  return request;
}

function routeContext(path: string[]): RouteContext {
  return { params: Promise.resolve({ path }) };
}
