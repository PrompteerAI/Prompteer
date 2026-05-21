import { createPrompteerApiClient, unwrapApiResponse } from "./api-client";
import { authGatewayOrigin } from "./env";
import { cookies } from "next/headers";
import type { components } from "@prompteer/shared-types";

export type BoardFeed = components["schemas"]["BoardFeedRead"];
export type Challenge = components["schemas"]["ChallengeRead"];
export type ChallengeTag = components["schemas"]["ChallengeTag"];
export type FeatureFlags = components["schemas"]["FeatureFlagsRead"];
export type IntegrationModes = components["schemas"]["IntegrationModesRead"];
export type BillingSubscription =
  components["schemas"]["BillingSubscriptionRead"];

export async function readChallenges(tag?: ChallengeTag): Promise<Challenge[]> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.GET("/api/v1/challenges", {
      params: tag ? { query: { tag } } : undefined,
      cache: "no-store",
    }),
  );
}

export async function readChallenge(id: string): Promise<Challenge> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.GET("/api/v1/challenges/{challenge_id}", {
      params: { path: { challenge_id: id } },
      cache: "no-store",
    }),
  );
}

export async function readBoard(limit = 12): Promise<BoardFeed> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.GET("/api/v1/community/board", {
      params: { query: { limit } },
      cache: "no-store",
    }),
  );
}

export async function readFeatures(): Promise<FeatureFlags> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.GET("/api/v1/config/features", { cache: "no-store" }),
  );
}

export async function readIntegrations(): Promise<IntegrationModes> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.GET("/api/v1/config/integrations", { cache: "no-store" }),
  );
}

export async function readBillingSubscription(): Promise<BillingSubscription | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) {
    return null;
  }

  const response = await fetch(
    `${authGatewayOrigin()}/api/backend/api/v1/billing/subscription`,
    {
      headers: {
        accept: "application/json",
        cookie: cookieHeader,
      },
      cache: "no-store",
    },
  );

  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Billing subscription request failed: ${response.status}`);
  }

  return (await response.json()) as BillingSubscription;
}
