// Unit tests for API error normalization, including openapi-fetch responses
// where the body has already been parsed before the UI sees the error.
import { describe, expect, it } from "vitest";

import { ApiResponseError, unwrapApiResponse } from "./api-client";
import { formatMutationError, normalizeError } from "./errors";

const problem = {
  type: "https://prompteer.dev/errors/rate-limited",
  title: "Too Many Requests",
  status: 429,
  detail: "Slow down.",
  instance: "/api/v1/challenges/123/run",
  code: "rate_limited",
  request_id: "req-123",
};

describe("normalizeError", () => {
  it("uses the parsed Problem Details body preserved by unwrapApiResponse", async () => {
    const response = new Response(null, { status: 429 });

    let caught: unknown;
    try {
      unwrapApiResponse({ error: problem, response });
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(ApiResponseError);
    expect((caught as ApiResponseError).body).toBe(problem);
    await expect(normalizeError(caught)).resolves.toMatchObject({
      code: "rate_limited",
      message: "Slow down.",
      status: 429,
      requestId: "req-123",
    });
  });

  it("falls back to HTTP metadata when the response body is unavailable", async () => {
    const response = new Response(null, {
      status: 502,
      statusText: "Bad Gateway",
      headers: { "x-request-id": "req-header-502" },
    });

    await expect(
      normalizeError(new ApiResponseError(response)),
    ).resolves.toMatchObject({
      code: "http_error",
      message: "Bad Gateway",
      status: 502,
      requestId: "req-header-502",
    });
  });

  it("parses Problem Details from an unconsumed response body", async () => {
    const problemWithoutRequestId = {
      type: problem.type,
      title: problem.title,
      status: problem.status,
      detail: problem.detail,
      instance: problem.instance,
      code: problem.code,
    };
    const response = new Response(JSON.stringify(problem), {
      status: 429,
      headers: {
        "content-type": "application/problem+json",
        "x-request-id": "req-header-429",
      },
    });
    const responseWithoutBodyRequestId = new Response(
      JSON.stringify(problemWithoutRequestId),
      {
        status: 429,
        headers: {
          "content-type": "application/problem+json",
          "x-request-id": "req-header-429",
        },
      },
    );

    await expect(
      normalizeError(new ApiResponseError(responseWithoutBodyRequestId)),
    ).resolves.toMatchObject({
      code: "rate_limited",
      requestId: "req-header-429",
    });

    await expect(
      normalizeError(new ApiResponseError(response)),
    ).resolves.toMatchObject({
      code: "rate_limited",
      message: "Slow down.",
      status: 429,
      requestId: "req-123",
    });
  });

  it("parses Retry-After seconds from Problem Details responses", async () => {
    const response = new Response(JSON.stringify(problem), {
      status: 429,
      headers: {
        "content-type": "application/problem+json",
        "retry-after": "17",
      },
    });

    await expect(
      normalizeError(new ApiResponseError(response)),
    ).resolves.toMatchObject({
      code: "rate_limited",
      retryAfterSeconds: 17,
      status: 429,
    });
  });

  it("formats mutation errors with detail and request id", () => {
    expect(
      formatMutationError(
        {
          code: "rate_limited",
          message: "Try again in 17 seconds.",
          requestId: "req-format",
        },
        "Prompt run failed.",
      ),
    ).toBe(
      "Prompt run failed. Detail: Try again in 17 seconds. Request ID: req-format",
    );
  });
});
