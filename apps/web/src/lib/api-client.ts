import { env } from "./env";

export class ApiResponseError extends Error {
  constructor(public readonly response: Response) {
    super(response.statusText || "API request failed");
    this.name = "ApiResponseError";
  }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    headers: {
      accept: "application/json",
      ...init?.headers
    }
  });

  if (!response.ok) {
    throw new ApiResponseError(response);
  }

  return (await response.json()) as T;
}
