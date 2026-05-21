import { createPrompteerApiClient, unwrapApiResponse } from "./api-client";
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
