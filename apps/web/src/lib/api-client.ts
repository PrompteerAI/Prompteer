import { env } from "./env";

export class ApiResponseError extends Error {
  constructor(public readonly response: Response) {
    super(response.statusText || "API request failed");
    this.name = "ApiResponseError";
  }
}

function apiBaseUrl(): string {
  if (typeof window !== "undefined") {
    return "/api/backend";
  }
  return env.NEXT_PUBLIC_API_URL;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: {
      accept: "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiResponseError(response);
  }

  return (await response.json()) as T;
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    method: "POST",
    headers: {
      accept: "application/json",
      "content-type": "application/json",
      ...init?.headers,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new ApiResponseError(response);
  }

  return (await response.json()) as T;
}
