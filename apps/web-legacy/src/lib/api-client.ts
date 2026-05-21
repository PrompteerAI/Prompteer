// OpenAPI-backed fetch wrapper. Browser calls use the legacy app's same-origin
// proxy, which forwards through the primary web app's authenticated API gateway.
import createClient from "openapi-fetch";
import type { Client } from "openapi-fetch";

import { getServerEnv } from "./env";
import type { paths } from "@prompteer/shared-types";

export class ApiResponseError extends Error {
  constructor(
    public readonly response: Response,
    public readonly body?: unknown,
  ) {
    super(response.statusText || "API request failed");
    this.name = "ApiResponseError";
  }
}

type ApiClient = Client<paths>;

type ApiResult<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

export function createPrompteerApiClient(): ApiClient {
  return createClient<paths>({
    baseUrl: openApiBaseUrl(),
  });
}

export function unwrapApiResponse<T>(result: ApiResult<T>): NonNullable<T> {
  if (result.error) {
    throw new ApiResponseError(result.response, result.error);
  }
  if (result.data === undefined) {
    throw new ApiResponseError(result.response);
  }
  return result.data as NonNullable<T>;
}

export function stripApiV1Prefix(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "").replace(/\/api\/v1$/, "");
}

function openApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    return "/api/backend";
  }

  const serverEnv = getServerEnv();
  return stripApiV1Prefix(
    serverEnv.API_INTERNAL_URL || serverEnv.NEXT_PUBLIC_API_URL,
  );
}
