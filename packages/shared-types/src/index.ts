import type { components } from "./api";

export type { components, operations, paths } from "./api";

export type ChallengeTag = components["schemas"]["ChallengeTag"];

export type FeatureFlags = components["schemas"]["FeatureFlagsRead"];

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  code: string;
  request_id?: string | null;
  errors?: Array<Record<string, unknown>>;
}
