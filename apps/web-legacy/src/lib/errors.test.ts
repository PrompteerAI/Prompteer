// Unit tests for the legacy-preview Problem Details normalizer.
import { describe, expect, it } from "vitest";

import { ApiResponseError } from "./api-client";
import { formatMutationError, normalizeError } from "./errors";

describe("legacy normalizeError", () => {
  it("uses the response request id header when Problem Details omits request_id", async () => {
    const response = new Response(
      JSON.stringify({
        code: "auth_gateway_unavailable",
        detail: "The primary web auth gateway is unavailable.",
        status: 502,
      }),
      {
        status: 502,
        headers: {
          "content-type": "application/problem+json",
          "x-request-id": "req-legacy-header",
        },
      },
    );

    await expect(
      normalizeError(new ApiResponseError(response)),
    ).resolves.toMatchObject({
      code: "auth_gateway_unavailable",
      message: "The primary web auth gateway is unavailable.",
      requestId: "req-legacy-header",
      status: 502,
    });
  });

  it("formats mutation errors with detail and request id", () => {
    expect(
      formatMutationError(
        {
          code: "dev_login_failed",
          message:
            "The primary web auth gateway rejected the dev login request.",
          requestId: "req-legacy-format",
        },
        "Checkout failed.",
      ),
    ).toBe(
      "Checkout failed. Detail: The primary web auth gateway rejected the dev login request. Request ID: req-legacy-format",
    );
  });
});
