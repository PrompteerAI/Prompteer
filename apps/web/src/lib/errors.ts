// Client-side API error normalization. Converts Problem Details and transport
// failures into stable codes that UI components can switch on.
import type { ProblemDetails } from "@prompteer/shared-types";

import { ApiResponseError } from "./api-client";

export type NormalizedError = {
  code: string;
  message: string;
  status?: number;
  requestId?: string | null;
  problem?: ProblemDetails;
};

export async function normalizeError(error: unknown): Promise<NormalizedError> {
  if (error instanceof ApiResponseError) {
    const contentType = error.response.headers.get("content-type") ?? "";
    if (contentType.includes("application/problem+json")) {
      const problem = (await error.response.json()) as ProblemDetails;
      return {
        code: problem.code,
        message: problem.detail,
        status: problem.status,
        requestId: problem.request_id,
        problem,
      };
    }
    return {
      code: "http_error",
      message: error.response.statusText,
      status: error.response.status,
    };
  }

  if (error instanceof Error) {
    return { code: "client_error", message: error.message };
  }

  return { code: "unknown_error", message: "Something went wrong." };
}
