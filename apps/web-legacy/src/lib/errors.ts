// Small Problem Details normalizer for legacy-preview client actions.
import { ApiResponseError } from "./api-client";

export interface NormalizedError {
  code: string;
  message: string;
  requestId?: string;
  status?: number;
}

export async function normalizeError(error: unknown): Promise<NormalizedError> {
  if (error instanceof ApiResponseError) {
    const body = error.body ?? (await safeJson(error.response));
    if (isProblemDetails(body)) {
      return {
        code: body.code,
        message: body.detail,
        requestId: body.request_id ?? undefined,
        status: body.status,
      };
    }
    return {
      code: "api_error",
      message: error.response.statusText || "API request failed.",
      status: error.response.status,
    };
  }

  if (error instanceof Error) {
    return { code: "unknown_error", message: error.message };
  }

  return { code: "unknown_error", message: "An unknown error occurred." };
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.clone().json();
  } catch {
    return undefined;
  }
}

function isProblemDetails(value: unknown): value is {
  code: string;
  detail: string;
  request_id?: string | null;
  status: number;
} {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "detail" in value &&
    typeof value.code === "string" &&
    typeof value.detail === "string"
  );
}
