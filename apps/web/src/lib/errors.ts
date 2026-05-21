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
    const problem =
      problemDetailsFromUnknown(error.body) ??
      (await problemDetailsFromResponse(error.response));
    if (problem) {
      return normalizeProblemDetails(problem);
    }

    return {
      code: "http_error",
      message:
        error.response.statusText ||
        `HTTP ${String(error.response.status)} request failed.`,
      status: error.response.status,
    };
  }

  if (error instanceof Error) {
    return { code: "client_error", message: error.message };
  }

  return { code: "unknown_error", message: "Something went wrong." };
}

function normalizeProblemDetails(problem: ProblemDetails): NormalizedError {
  return {
    code: problem.code,
    message: problem.detail,
    status: problem.status,
    requestId: problem.request_id,
    problem,
  };
}

async function problemDetailsFromResponse(
  response: Response,
): Promise<ProblemDetails | undefined> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/problem+json")) {
    return undefined;
  }

  try {
    return problemDetailsFromUnknown(await response.clone().json());
  } catch {
    return undefined;
  }
}

function problemDetailsFromUnknown(value: unknown): ProblemDetails | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }

  const candidate = value as Partial<ProblemDetails>;
  if (
    typeof candidate.type !== "string" ||
    typeof candidate.title !== "string" ||
    typeof candidate.status !== "number" ||
    typeof candidate.detail !== "string" ||
    typeof candidate.instance !== "string" ||
    typeof candidate.code !== "string"
  ) {
    return undefined;
  }

  return {
    type: candidate.type,
    title: candidate.title,
    status: candidate.status,
    detail: candidate.detail,
    instance: candidate.instance,
    code: candidate.code,
    request_id: candidate.request_id,
    errors: candidate.errors,
  };
}
